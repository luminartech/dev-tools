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
