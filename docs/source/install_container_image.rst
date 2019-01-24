.. _container:

Installing the Quipucords Server Container Image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After Docker is installed, you can obtain and install the container image that enables the use of the Quipucords server.

1. Download the server container image by entering the following command::

    # curl -k -O -sSL https://github.com/quipucords/quipucords/releases/download/0.0.46/quipucords.0.0.46.tar.gz


2. Load the container image into the local Docker registry with the following command::

    # sudo docker load -i quipucords.0.0.46.tar.gz

The output appears similar to the following example::

    Loaded image: quipucords:0.0.46


3. Verify the image within the local Docker registry by entering the following command::

    # sudo docker images

The output appears similar to the following example::

  REPOSITORY              TAG                 IMAGE ID            CREATED             SIZE
  quipucords              0.0.46               fdadcc4b326f        3 days ago          969MB


.. _postgres-image-create:

How to Create a Postgres Image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. After Docker is installed, you can obtain the postgres container image with these steps::

    docker pull postgres:9.6.10
    docker save -o postgres.9.6.10.tar postgres:9.6.10

**Note:** These steps do require the use of the internet.

2. Follow the same steps start at number two from above to load the image into the environment. 
