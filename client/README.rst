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

3. Set up and run the mock API::

    $ npm run api:mock

Development Server & Mock API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To run the development server, use this command::

    $ npm run start:client

Unit Tests
^^^^^^^^^^
To run the unit tests, use this command::

    $ npm test

Building the UI
^^^^^^^^^^^^^^^
The UI is compiled for production within a `client` directory underneath `./quipucords/client`. To build the UI, use this command::

    $ npm run build:prod


Serving the UI
^^^^^^^^^^^^^^
If you've gone through the Python quipucords installation you can serve the UI and API with this command::

    $ npm run start:quipucords

*This NPM script is not intended as a replacement for serving the application, but as a shortcut during development.*

