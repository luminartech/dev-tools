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

### Testing the hooks on another repo

```shell
poetry run <hook_name> <hook_args>
# Eg. poetry run check-ownership --codeowners-owner your_github_user --repo-dir ../other-repo/
```
