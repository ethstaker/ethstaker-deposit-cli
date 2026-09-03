import asyncio
import os
import re

ANSI_ESCAPE_PATTERN = re.compile(
    r'\x1b(?:'
    r'\[[0-9;?]*[A-Za-z]'              # CSI sequences (cursor movement, colors, ...)
    r'|\][^\x07]*(?:\x07|\x1b\\)'      # OSC sequences (window title, ...)
    r'|[@-Z\\-_=>c78]'                 # other two-byte escape sequences (e.g. \x1bc full reset)
    r')'
)

DEFAULT_READ_TIMEOUT = 60.0
DEFAULT_EXPECT_TIMEOUT = 120.0
DEFAULT_EXIT_TIMEOUT = 300.0


class InteractiveProcess:
    '''
    Expect-style helper for running the CLI as a subprocess with piped stdin/stdout
    and simulating user interaction.

    Robustness properties compared to hand-rolled scraping:
    - every read and the exit wait are bounded by timeouts, so a missing prompt
      fails fast instead of hanging the whole test suite;
    - ANSI escape sequences are stripped before matching;
    - prompts are located by substring instead of exact line prefixes;
    - stderr is merged into stdout and all observed lines are kept in a
      transcript that is included in failure messages;
    - the exit code is asserted to be 0 by `wait()`;
    - the subprocess is killed if the test fails while it is still running.

    Only one interaction currently exists in the `--non_interactive` flows:
    the mnemonic retype `click.prompt`. The `click.pause()` calls in the CLI
    ("press any key", clipboard clearing) are no-ops and print nothing when
    stdin/stdout are not TTYs (verified against click's implementation), so
    they require no simulated input here.
    '''

    def __init__(
        self,
        command: str,
        *,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
        expect_timeout: float = DEFAULT_EXPECT_TIMEOUT,
        exit_timeout: float = DEFAULT_EXIT_TIMEOUT,
    ) -> None:
        self._command = command
        self._read_timeout = read_timeout
        self._expect_timeout = expect_timeout
        self._exit_timeout = exit_timeout
        self.transcript: list[str] = []
        self._process: asyncio.subprocess.Process | None = None

    async def __aenter__(self) -> 'InteractiveProcess':
        env = os.environ.copy()
        # PYTEST_CURRENT_TEST is deliberately kept in the child environment:
        # ethstaker_deposit.utils.terminal.clear_terminal() skips clearing under
        # pytest. Without it, the child would run `clear`/`tput reset`/`reset`
        # writing ANSI sequences into the pipe we scrape, which the stripping in
        # readline() defends against but which we should not rely on.
        self._process = await asyncio.create_subprocess_shell(  # noqa: S602
            self._command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._process is not None and self._process.returncode is None:
            self._process.kill()
            await self._process.wait()

    def fail(self, message: str) -> AssertionError:
        '''
        Build an AssertionError including the recent subprocess output.
        '''
        tail = '\n'.join(self.transcript[-100:])
        return AssertionError(f'{message}\n--- subprocess output ---\n{tail}')

    async def readline(self) -> str | None:
        '''
        Read one line of subprocess output with ANSI escapes stripped.
        Returns None on EOF.
        '''
        if self._process is None:
            raise RuntimeError('InteractiveProcess was not started')
        try:
            raw = await asyncio.wait_for(
                self._process.stdout.readline(),
                timeout=self._read_timeout,
            )
        except TimeoutError as e:
            raise self.fail(
                f'Timed out after {self._read_timeout}s waiting for subprocess output'
            ) from e
        if not raw:
            return None
        line = ANSI_ESCAPE_PATTERN.sub('', raw.decode('utf-8', errors='replace')).rstrip('\r\n')
        self.transcript.append(line)
        return line

    async def expect(self, substring: str, timeout: float | None = None) -> str:
        '''
        Read lines until one contains `substring`; returns the matching line.
        Raises if the subprocess exits or the timeout expires first.
        '''
        effective_timeout = timeout if timeout is not None else self._expect_timeout
        loop = asyncio.get_running_loop()
        deadline = loop.time() + effective_timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise self.fail(f'Did not see {substring!r} within {effective_timeout}s')
            try:
                line = await self.readline_with_timeout(remaining)
            except AssertionError as e:
                # readline() only raises AssertionError on a read timeout.
                raise self.fail(f'Did not see {substring!r} within {effective_timeout}s') from e
            if line is None:
                raise self.fail(
                    f'Subprocess exited before {substring!r} was seen (exit code {self._process.returncode})'
                )
            if substring in line:
                return line

    async def readline_with_timeout(self, timeout: float) -> str | None:
        saved_timeout = self._read_timeout
        self._read_timeout = timeout
        try:
            return await self.readline()
        finally:
            self._read_timeout = saved_timeout

    async def sendline(self, text: str) -> None:
        '''
        Write one line to the subprocess stdin, simulating user input.
        '''
        stdin = self._process.stdin
        stdin.write(text.encode('utf-8') + b'\n')
        await stdin.drain()

    async def wait(self) -> None:
        '''
        Wait for the subprocess to exit and assert a zero exit code.
        '''
        try:
            await asyncio.wait_for(self._process.wait(), timeout=self._exit_timeout)
        except TimeoutError as e:
            self._process.kill()
            await self._process.wait()
            raise self.fail(
                f'Subprocess did not exit within {self._exit_timeout}s'
            ) from e
        if self._process.returncode != 0:
            raise self.fail(f'Subprocess exited with code {self._process.returncode}')
