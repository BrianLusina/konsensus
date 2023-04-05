# Konsensus

[![Lint](https://github.com/BrianLusina/konsensus/actions/workflows/lint.yml/badge.svg)](https://github.com/BrianLusina/konsensus/actions/workflows/lint.yml)
[![Tests](https://github.com/BrianLusina/konsensus/actions/workflows/tests.yaml/badge.svg)](https://github.com/BrianLusina/konsensus/actions/workflows/tests.yaml)
[![codecov](https://codecov.io/gh/BrianLusina/konsensus/branch/main/graph/badge.svg?token=8GkDyydZdQ)](https://codecov.io/gh/BrianLusina/konsensus)
[![Build](https://github.com/BrianLusina/konsensus/actions/workflows/build.yaml/badge.svg)](https://github.com/BrianLusina/konsensus/actions/workflows/build.yaml)
[![Publish](https://github.com/BrianLusina/konsensus/actions/workflows/publish.yaml/badge.svg)](https://github.com/BrianLusina/konsensus/actions/workflows/publish.yaml)
[![CodeQL](https://github.com/BrianLusina/konsensus/actions/workflows/codeql.yaml/badge.svg)](https://github.com/BrianLusina/konsensus/actions/workflows/codeql.yaml)
[![Version](https://img.shields.io/github/v/release/brianlusina/konsensus?color=%235351FB&label=version)](https://github.com/brianlusina/konsensus/releases)
[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)

A simple clustering by consensus library in Python. This is a simple implementation of a replicated state machine
using a Paxos-derived algorithm.

## Getting Started

Ensure you have the following first before you proceed:

1. [Python 3.10+](https://www.python.org/)

   You will require Python 3.10+ to run this project. If you are using a different version of Python, you will need to
   update your Python version to 3.10+. You can check your Python version by running `python --version`
   in your terminal. There are ways to install different versions of Python on your system and this can be done using
   [pyenv](https://github.com/pyenv/pyenv).

2. [Poetry](https://python-poetry.org/)

   Poetry is a Python package manager that is used to manage dependencies. You can check the installation instructions
   in
   the link provided to get this setup.

3. [Virtualenv](https://virtualenv.pypa.io/)

   Not a hard requirement as poetry should setup a virtual environment for you, but can be used as well to setup a
   virtual environment.

Once you have dependencies setup, run the below command to install dependencies:

```shell
poetry install
```

> Even though this implementation has 0 dependencies to external packages, the dev packages are used for linting &
> handling
> tests. Therefore, this is useful when running linting & test commands.

The library itself is in the [konsensus](./konsensus) directory.

## Running

There is a simple script in the project root [run.py](./run.py) that contains a sample setup on how to use the library.
It can be run with:

```shell
python run.py 10
```

> _10_ is the seed value, this can be any other value like 20 or 30, etc

There are other scripts available in the [Makefile](./Makefile) that can be used to run formatting, linting, test or
build commands.

## Built With

| Tool   | Purpose                      |
|--------|------------------------------|
| Python | Programming Language         |
| Poetry | Dependency & Package manager |

## Contributing

Please read the [contributing guide](./.github/CONTRIBUTING.md) to learn how to contribute to this project.

## Versioning

[Semantic versioning](https://semver/) is used to track the version of the project.
