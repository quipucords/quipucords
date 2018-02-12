Quipucords UI
=============

User interface for Quipucords. This project was bootstrapped with `Create React App <https://github.com/facebookincubator/create-react-app>`_.

Requirements
------------
Before developing for Quipucords UI, here are some basic guidelines:
 * Your system needs to be running `NodeJS version 6+ <https://nodejs.org/>`_
 * To run the mock API, your system needs to be running `Docker <https://docs.docker.com/engine/installation/>`_

Development
-----------

Installing
^^^^^^^^^^
1. Clone the repository::

    $ git clone git@github.com:quipucords/quipucords.git

2. Within the quipucords repo, install project dependencies::

    $ cd client
    $ npm install

Development Server & Mock API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To run the development server and mock API, use this command::

    $ npm start

If you have Docker running, this will automatically setup the mock API.

Mock API
********
To setup the mock API separately you can run::

    $ npm run api:mock

Debugging Redux
***************
This project makes use of React & Redux. To enable Redux console logging, within the `client` directory, add a `.env.local` (dotenv) file with the follow line::

  REACT_APP_DEBUG_MIDDLEWARE=true

Once you've made the change, restart the project and console browser logging should appear.


*Any changes you make to the `.env.local` file should be ignored with `.gitignore`.*

Unit Tests
^^^^^^^^^^
To run the unit tests, use this command::

    $ npm test

Building the Production UI
^^^^^^^^^^^^^^^^^^^^^^^^^^
The UI is compiled for production within a `client` directory underneath `./quipucords/client`. To build the UI, use this command::

    $ npm run build:prod

Serving the Production UI & API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you've gone through the Python quipucords installation you can serve the UI and API with this command::

    $ npm run start:quipucords

Using Docker
************
If you'd rather run quipucords through Docker you can serve the UI and API with this set of commands::

    $ docker stop quipucords || docker ps && npm run api:update && npm run api:quipucords


*This set of NPM scripts are not intended as a replacement for serving the application, but as a shortcut during development.*

