# Contributing to quipucords

Bug reports and code and documentation patches are welcome. You can
help this project also by using the development version of quipucords
and by reporting any bugs you might encounter.

## Reporting issues

Development of quipucords feature requests and bugs are handled under the `DISCOVERY` project in Red Hat's JIRA instance. You may find current issues at:

https://issues.redhat.com/projects/DISCOVERY/issues

If you have a bug to report, when submitting an issue, provide the following information:

* Provide a detailed description of the running environment including software and OS versions.
* List the exact steps you can take to reproduce and observe the bug.
* Describe what you observe to be the bug at that point.
* Describe what you expected to happen instead.
* Attach all logs from your running instance to the issue.
    * However, you should review logs before attaching and be careful not to publicly post any private or sensitive information.
* Attach any relevant report tar.gz files to the issue.
* Attach any relevant screenshots to the issue.

Failure to include detailed descriptions and logs may result in the development team closing the issue with no further action.

## Development environment

Follow the instructions in [README](README.md) to set up your local development environment.

## Submitting code

Before opening a pull request, your work must be committed in a new branch off of `main`, and your branch should have a unique, short, and relevant name for the changes you propose.

All changes should conform to [PEP8 Style Guide for Python Code](http://python.org/dev/peps/pep-0008/), and all unit tests must pass. Run the following make targets locally on your branch to verify:

```
make lint
make test
```

To check coverage of unit tests, run:

```
make test-coverage
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

### Update dependencies
There's a dedicated make target for easily updating ALL lockfiles and base image digests on the Containerfile
```
make update-lockfiles
```
Besides python dependencies required for development, this command also requires `podman`, `skopeo`, `yq` (the go version, not the on on pypi),
[`konflux-pipeline-patcher`](https://github.com/simonbaird/konflux-pipeline-patcher) and, if you are on macOS, `gsed`.

-----

See [Makefile](Makefile) for additional development utilities.
