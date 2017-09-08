######################
Contributing to quipucords
######################

Bug reports and code and documentation patches are welcome. You can
help this project also by using the development version of quipucords
and by reporting any bugs you might encounter.

1. Reporting bugs
=================

It's important that you provide the full explanation of the failure along
with recreation steps, environment information, and any associated logs


2. Contributing Code and Docs
=============================

Before working on a new feature or a bug, please browse `existing issues`_
to see whether it has been previously discussed. If the change in question
is a bigger one, it's always good to discuss before you starting working on
it.


Creating Development Environment
--------------------------------

Go to https://github.com/quipucords/quipucords and fork the project repository. Each
branch should correspond to an associated issue opened on the main repository
(e.g. ``issues/5`` --> https://github.com/quipucords/quipucords/issues/5).


.. code-block:: bash

    git clone https://github.com/<YOU>/quipucords

    cd quipucords

    git checkout -b issues/my_issue_#

    pip install -r requirements.txt

    make all


Making Changes
--------------

Please make sure your changes conform to `Style Guide for Python Code`_ (PEP8).
You can run the lint command on your branch to check compliance.

.. code-block:: bash

    make lint

Testing
-------

Before opening a pull requests, please make sure the `tests`_ pass
in all of the supported Python environments (3.5, 3.6).
You should also add tests for any new features and bug fixes.

quipucords uses `pytest`_ for testing.


Running all tests:
******************

.. code-block:: bash

    # Run all tests on the current Python interpreter
    make tests

    # Run all tests on the current Python with coverage
    make tests-coverage


-----

See `Makefile`_ for additional development utilities.

.. _existing issues: https://github.com/quipucords/quipucords/issues?state=open
.. _AUTHORS: https://github.com/quipucords/quipucords/blob/master/AUTHORS.rst
.. _Makefile: https://github.com/quipucords/quipucords/blob/master/Makefile
.. _pytest: http://pytest.org/
.. _Style Guide for Python Code: http://python.org/dev/peps/pep-0008/
