# Contributing to quipucords

Bug reports and code and documentation patches are welcome. You can
help this project also by using the development version of quipucords
and by reporting any bugs you might encounter.

## Reporting bugs
It's important that you provide the full explanation of the failure along
with recreation steps, environment information, and any associated logs


## Contributing Code and Docs
Before working on a new feature or a bug, please browse [existing issues](https://github.com/quipucords/quipucords/issues?state=open)
to see whether it has been previously discussed. If the change in question
is a bigger one, it's always good to discuss before you start working on
it.


### Creating Development Environment

Go to https://github.com/quipucords/quipucords and fork the project repository. Each
branch should correspond to an associated issue opened on the main repository
(e.g. `issues/5` --> https://github.com/quipucords/quipucords/issues/5).


```
git clone https://github.com/quipucords/quipucords
cd quipucords
git checkout -b issues/my_issue_#
pip install -r dev-requirements.txt
```

### Making Changes
Please make sure your changes conform to [Style Guide for Python Code](http://python.org/dev/peps/pep-0008/) (PEP8).
You can run the lint command on your branch to check compliance.
```
make lint
```

### Testing
Before opening a pull requests, please make sure the tests pass
in a Python 3.9 environments.
You should also add tests for any new features and bug fixes.

quipucords uses [pytest](http://pytest.org/) for testing.


### Running Tests
Run all tests on the current Python interpreter
```
make test
```
Run all tests on the current Python with coverage
```
make test-coverage
```

-----

See [Makefile](https://github.com/quipucords/quipucords/blob/master/Makefile) for additional development utilities.
