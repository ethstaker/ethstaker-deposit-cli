VENV_NAME?=venv
PYTHON?=python3
BUILD_PYTHON?=python3.14
VENV_PYTHON=$(VENV_NAME)/bin/python
PYPROJECT=pyproject.toml
BUILD_PYTHON_MAJOR=3
BUILD_PYTHON_MINOR=14
DOCKER_IMAGE="ghcr.io/ethstaker/ethstaker-deposit-cli:latest"

.PHONY: help clean venv_build venv_build_test venv_test venv_lint venv_deposit \
	build_macos build_linux build_docker run_docker binary_venv binary_test

help:
	@echo "clean - remove build and Python file artifacts"
	# Run with venv
	@echo "venv_deposit - run deposit cli with venv"
	@echo "venv_build - install basic dependencies with venv"
	@echo "venv_build_test - install testing dependencies with venv"
	@echo "venv_lint - check style with ruff and mypy with venv"
	@echo "venv_test - run tests with venv"
	@echo "binary_test - build a standalone binary and run the binary_tests release-asset suite with expect"

clean:
	rm -rf venv/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .tox/
	find . -path './.venv' -prune -o -type d \( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache \) -prune -exec rm -rf {} +

$(VENV_NAME)/bin/activate: requirements.txt $(PYPROJECT)
	@$(PYTHON) scripts/check_python_version.py $(PYPROJECT)
	@if test -x $(VENV_PYTHON) && test "$$($(VENV_PYTHON) -c 'import sys; print(sys.executable)')" != "$$($(PYTHON) -c 'import sys; print(sys.executable)')"; then \
		echo "$(VENV_NAME) was created with a different Python interpreter; recreating it."; \
		rm -rf $(VENV_NAME); \
	fi
	@test -d $(VENV_NAME) || $(PYTHON) -m venv $(VENV_NAME)
	@$(VENV_PYTHON) scripts/check_python_version.py $(PYPROJECT)
	$(VENV_PYTHON) -m pip install --require-hashes -r requirements.txt -r requirements_test.txt
	@touch $(VENV_NAME)/bin/activate

venv_build: $(VENV_NAME)/bin/activate

venv_build_test: venv_build
	$(VENV_PYTHON) -m pip install --require-hashes -r requirements.txt -r requirements_test.txt

venv_test: venv_build_test
	$(VENV_PYTHON) -m pytest ./tests

venv_lint: venv_build_test
	$(VENV_PYTHON) -m ruff check ./ethstaker_deposit ./tests && $(VENV_PYTHON) -m mypy --config-file mypy.ini -p ethstaker_deposit
	$(VENV_PYTHON) scripts/check_dependencies_sync.py

venv_deposit: venv_build
	$(VENV_PYTHON) -m ethstaker_deposit $(filter-out $@,$(MAKECMDGOALS))

build_macos: PYTHON=$(BUILD_PYTHON)
build_macos: binary_venv
	@command -v $(BUILD_PYTHON) >/dev/null 2>&1 || { echo "Binary builds require Python 3.14. Install python3.14 or run make BUILD_PYTHON=/path/to/python3.14 build_macos." >&2; exit 1; }
	$(VENV_PYTHON) -m pip install --require-hashes -r ./build_configs/macos/requirements.txt
	PYTHONHASHSEED=42 $(VENV_PYTHON) -m PyInstaller ./build_configs/macos/build.spec

build_linux: PYTHON=$(BUILD_PYTHON)
build_linux: binary_venv
	@command -v $(BUILD_PYTHON) >/dev/null 2>&1 || { echo "Binary builds require Python 3.14. Install python3.14 or run make BUILD_PYTHON=/path/to/python3.14 build_linux." >&2; exit 1; }
	$(VENV_PYTHON) -m pip install --require-hashes -r ./build_configs/linux/requirements.txt
	PYTHONHASHSEED=42 $(VENV_PYTHON) -m PyInstaller ./build_configs/linux/build.spec

binary_venv: PYTHON=$(BUILD_PYTHON)
binary_venv:
	@command -v $(BUILD_PYTHON) >/dev/null 2>&1 || { echo "Binary builds require Python 3.14. Install python3.14 or run make BUILD_PYTHON=/path/to/python3.14." >&2; exit 1; }
	@$(PYTHON) scripts/check_python_version.py $(PYPROJECT)
	@if test -x $(VENV_PYTHON) && test "$$($(VENV_PYTHON) -c 'import sys; print(sys.version_info[:2])')" != "$$($(PYTHON) -c 'import sys; print(sys.version_info[:2])')"; then \
		echo "$(VENV_NAME) was created with a different Python version; recreating it."; \
		rm -rf $(VENV_NAME); \
	fi
	@test -d $(VENV_NAME) || $(PYTHON) -m venv $(VENV_NAME)
	@$(VENV_PYTHON) -c 'import sys; expected=($(BUILD_PYTHON_MAJOR), $(BUILD_PYTHON_MINOR)); actual=sys.version_info[:2]; sys.exit(0 if actual == expected else "Binary builds require Python 3.14")'
	$(VENV_PYTHON) -m pip install --require-hashes -r requirements.txt

# Build a standalone binary for the current platform and run the
# interactive release-asset tests from binary_tests/ against it with expect.
# Requires `expect` on PATH.
binary_test:
	@os=$$(uname -s); \
	if [ "$$os" = "Linux" ]; then \
		$(MAKE) build_linux; \
	elif [ "$$os" = "Darwin" ]; then \
		$(MAKE) build_macos; \
	else \
		echo "binary_test is only supported on Linux and macOS (got $$os)." >&2; \
		exit 1; \
	fi
	bash binary_tests/run_tests.sh ./dist

build_docker:
	@docker build --pull -t $(DOCKER_IMAGE) .

run_docker:
	@docker run -it --rm $(DOCKER_IMAGE) $(filter-out $@,$(MAKECMDGOALS))
