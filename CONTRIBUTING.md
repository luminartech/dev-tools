# Contributing

Contributions are welcome.
Feel free to open an issue in [our issue tracker](https://github.com/luminartech/dev-tools/issues) and/or create a pull request.

## Local Development

You need a Python interpreter and Poetry installed.
Then simply run

```shell
poetry install  # to setup your virtual environment with all dependencies
poetry run pytest  # to run all unit tests
```

To run a development version of a script for testing eg. a hook on another repo, run:

```shell
poetry install # to install current poetry scripts in a virtualenv
poetry shell # to activate the virtualenv
# And then eg.
cd <another_repo>
check-ownership file1 file2
```

An alternative to the above is to run:

```shell
pip3 install -e .
```

That will install the tools in editable mode, meaning that your code changes will be visible as soon as you run the scripts again.

## Creating a release

To release a new version of dev-tools:

1. update the pyproject.toml `version` field,
1. put up a PR and get it merged to master,
1. once merged, create a tag with the same version and push it,
1. a release pipeline will run automatically and push a release.
