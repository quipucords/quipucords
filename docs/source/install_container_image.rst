.. _container:

Installing the Quipucords Server Container Image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After Docker is installed, you can obtain and install the container image that enables the use of the Quipucords server.

1. Download the server container image by entering the following command::

    # curl -k -O -sSL https://github.com/quipucords/quipucords/releases/download/0.0.45/quipucords.0.0.45.tar.gz


2. Load the container image into the local Docker registry with the following command::

    # sudo docker load -i quipucords.0.0.45.tar.gz

The output appears similar to the following example::

    Loaded image: quipucords:0.0.45


3. Verify the image within the local Docker registry by entering the following command::

    # sudo docker images

The output appears similar to the following example::

  REPOSITORY              TAG                 IMAGE ID            CREATED             SIZE
  quipucords              0.0.45               fdadcc4b326f        3 days ago          969MB
