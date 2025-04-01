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
poetry install
```

### Making Changes
Please make sure your changes conform to [Style Guide for Python Code](http://python.org/dev/peps/pep-0008/) (PEP8).
You can run the lint command on your branch to check compliance.
```
make lint
```

### Debugging

You can easily attach a debugger to a container running quipucords server or celery worker.

For VSCode this can be achieved adding the following to `.vscode/launch.json`

```json

{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Container attach",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "0.0.0.0",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ]
        }

    ]
}
```

And since debugpy implements microsoft Debugger adapter protocol (DAP), a similar 
config can be done on other editors that support it:

https://microsoft.github.io/debug-adapter-protocol/implementors/tools/

### Testing
Before opening a pull requests, please make sure the tests pass
in a Python 3.9 environment.
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

### Update dependencies
There's a dedicated make target for easily updating ALL lockfiles and base image digests on the Containerfile
```
make update-lockfiles
```
Besides python dependencies required for development, this command also requires `podman`, `skopeo`, `yq` (the go version, not the on on pypi),
[`konflux-pipeline-patcher`](https://github.com/simonbaird/konflux-pipeline-patcher) and, if you are on macOS, `gsed`.

-----

See [Makefile](Makefile) for additional development utilities.
