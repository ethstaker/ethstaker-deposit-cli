# Release Process Instructions

This document is meant as a guide on how to perform and publish a new release version of [ethstaker-deposit-cli](https://github.com/ethstaker/ethstaker-deposit-cli). It includes step by step instructions to complete the release process.

1. Make sure all the tests from the latest [ci-runner workflow](https://github.com/ethstaker/ethstaker-deposit-cli/actions/workflows/runner.yml) on the latest commit of the main branch are completed. Make sure all tests are passing on all the supported platforms.
2. Determine a new version number. Version numbers should adhere to [Semantic Versioning](https://semver.org/). For any official release, it should include a major, a minor and a patch identifier like `1.0.0`. For a pre-release append a [PEP 440](https://peps.python.org/pep-0440/) pre-release identifier such as `rc1` e.g. `1.4.0-rc1`. This suffix is the only thing that makes PyPi treat the library package as a pre-release, and it can't be added or removed after the fact.
3. Update `ethstaker_deposit/VERSION`'s content with the new version number (including the pre-release suffix from step 2, if any). Commit this change to the main branch of the main repository. This is a hard requirement: [the ci-pypi workflow](https://github.com/ethstaker/ethstaker-deposit-cli/actions/workflows/pypi.yml) (see step 8 below) refuses to publish to PyPI if this file doesn't exactly match the tag pushed in the next step, or if its pre-release status doesn't match the *Set as a pre-release* checkbox in step 7.
4. Add a tag to the main repository for this changed version commit above. The name of this tag should be a string starting with `v` concatenated with the version number. With git, the main repository cloned and the commit above being the head, it can look like this:
```console
git tag -a -m 'Version 1.0.0' v1.0.0
git push origin v1.0.0
```
5. Wait for all the build assets and the draft release to be created by [the ci-build workflow](https://github.com/ethstaker/ethstaker-deposit-cli/actions/workflows/build.yml).
6. Open the draft release and fill in the different sections correctly.
7. Check the *Set as a pre-release* checkbox if and only if the version from step 2/3 carries a pre-release suffix — these must agree, or the ci-pypi workflow will refuse to publish in the next step.
8. Click the *Publish release* button. This triggers:
   - [the ci-pypi workflow](https://github.com/ethstaker/ethstaker-deposit-cli/actions/workflows/pypi.yml), which cross-checks the VERSION file's pre-release status against this release's *Set as a pre-release* flag, then builds and publishes the package to PyPI regardless of pre-release status. This workflow waits for approval against the `pypi` environment's protection rule — open the workflow run in the Actions tab and approve the pending deployment to let it proceed.
   - [the docker-latest workflow](https://github.com/ethstaker/ethstaker-deposit-cli/actions/workflows/docker-latest.yml), which points the `latest` Docker tag at this release's image — unless it was checked as a pre-release in step 7, in which case `latest` is left untouched.
9. Determine a new dev version number. You can try to guess the next version number to the best of your ability. This will always be subject to change. Add a `-dev` identifier to the version number.
10. Update `ethstaker_deposit/VERSION`'s content with a new dev version number. Commit this change to the main branch.

## Release Notes Template

You can find the latest release notes template on https://github.com/ethstaker/ethstaker-deposit-cli/blob/main/.github/release_template.md .
