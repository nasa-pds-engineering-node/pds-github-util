# 🏃‍♀️ Continuous Integration and Delivery: Unstable
# ===============================================
#
# Note: for this workflow to succeed, the following secrets must be installed
# in the repository:
#
# ``ADMIN_GITHUB_TOKEN``
#     A personal access token of a user with collaborator or better access to
#     the project repository. You can generate this by visiting GitHub →
#     Settings → Developer settings → Personal access tokens → Generate new
#     token. Give the token scopes on ``repo``, ``write:packages``,
#     ``delete:packages``, ``workflow``, and ``read:gpg_key``.
# ``PYPI_USERNAME``
#     Username for pypi.org.
# ``PYPI_PASSWORD``
#     Password for ``PYPI_USERNAME``.
#


---

name: Roundup action free unstable integration and delivery ⛔🐔and🥚


on:
    push:
        tag:
            - v*.*.*-rc*
            - v*


jobs:
    unstable-assembly:
        name: 🐴 Unstable Assembly
        runs-on: ubuntu-latest
        steps:
            -
                name: 💳 Checkout
                uses: actions/checkout@v2
                with:
                    lfs: true
                    token: ${{secrets.ADMIN_GITHUB_TOKEN}}
                    fetch-depth: 0
            -
                name: 💵 Python Cache
                uses: actions/cache@v2
                with:
                    path: ~/.cache/pip
                    # The "key" used to indicate a set of cached files is the operating system runner
                    # plus "py" for Python-specific builds, plus a hash of the wheels, plus "pds" because
                    # we pds-prefix everything with "pds" in PDS! 😅
                    key: pds-${{runner.os}}-py-${{hashFiles('**/*.whl')}}
                    # To restore a set of files, we only need to match a prefix of the saved key.
                    restore-keys: pds-${{runner.os}}-py-
            # Pretty much everything after this is likely not a great way to do this but ...
            # it's a work in progress ... so here we are.
            - 
                name: Set up Python 3.9
                uses: actions/setup-python@v1
                with:
                    python-version: 3.9
            -
                name: Prep for build
                run:
                    pip install wheel
            -
                name: Build Wheel
                run:
                    python setup.py bdist_wheel
            -
                name: Publish package to TestPyPI
                uses: pypa/gh-action-pypi-publish@release/v1
                with:
                    # Should really use PyPI's API token stuff here
                    user: ${{secrets.PYPI_USERNAME}}
                    password: ${{secrets.TEST_PYPI_API_TOKEN}}
                    repository_url: https://test.pypi.org/legacy/

            # -
                # # Send a respository dispatch to pds-actions-base to trigger
                # # a fresh build since it depends on pds-github-util
                # name: Trigger github-actions-base build
                # uses: peter-evans/repository-dispatch@v1
                # with:
                    # token: ${{secrets.ADMIN_GITHUB_TOKEN}}
                    # repository: NASA-PDS/github-actions-base
                    # event-type: pds-github-util-built
