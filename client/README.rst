Quipucords UI
=============

User interface for Quipucords. This project was bootstrapped with `Create React App <https://github.com/facebookincubator/create-react-app>`_.

Requirements
------------
Before developing for Quipucords UI, the requirements:
 * Your system needs to be running `NodeJS version 8+ <https://nodejs.org/>`_
 * And `Docker <https://docs.docker.com/engine/installation/>`_

Development
-----------

Installing
^^^^^^^^^^
1. Clone the repository::

    $ git clone git@github.com:quipucords/quipucords.git

2. Within the quipucords repo, install project dependencies::

    $ cd client
    $ npm install

Development Serve
^^^^^^^^^^^^^^^^^
To run the development server and API, use this command::

    $ npm start

If you have Docker running, this will automatically setup and start the development API.

Development API
***************
To setup the development API separately you can run::

    $ npm run api:dev

The development API produces randomized data against a Swagger spec.

Debugging Redux
***************
This project makes use of React & Redux. To enable Redux console logging, within the ``[REPO]/client`` directory, add a ``.env.local`` (dotenv) file with the follow line::

  REACT_APP_DEBUG_MIDDLEWARE=true

Once you've made the change, restart the project and console browser logging should appear.


*Any changes you make to the `.env.local` file should be ignored with `.gitignore`.*

Unit Tests
^^^^^^^^^^
To run the unit tests, use this command::

    $ npm test

Building the Production UI
^^^^^^^^^^^^^^^^^^^^^^^^^^
The UI is compiled for production within a ``client`` directory underneath ``[REPO]/quipucords/client``. To build the UI, use this command::

    $ npm run build

Using Docker
^^^^^^^^^^^^
The UI/UX team currently uses Docker to aid development.

Development Serve
*****************
This is the default context for running the UI::

    $ npm start

Staging Serve
*************
To run the build under a staging context against a production level quipucords API, use this command::

    $ npm run start:stage

The staging context allows development to continue by pointing Docker at the ``[REPO]/client/build`` directory.

Production Serve
****************
To run the existing build under a production context, use this command::

    $ npm run start:prod


*This set of NPM scripts are not intended as a replacement for serving the application, but as shortcuts during development.*

