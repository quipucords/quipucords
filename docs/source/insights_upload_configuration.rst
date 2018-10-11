Installing the Insights Client
------------------------------
To work with the Insights Client, we must also install the Insights Core. To begin, create the insights directory and clone the following repositories::

    mkdir insights && cd insights
    git clone git@github.com:RedHatInsights/insights-core.git
    git clone git@github.com:RedHatInsights/insights-client.git

Setting Up a Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We recommend that you isolate your development work by using a virtual environment. Run the following command to set up a virtual environment::

    pipenv shell

Accessing the Insights Development Branches
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For QPC to access the Insights Client locally we need to checkout branches that are still in development.

    `cd insights-core`
    `git fetch origin platform-upload && git checkout platform-upload`
    `cd ../insights-client`
    `git fetch origin os-x-test && git checkout os-x-test`

Edit the Insights Client Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You will need modify the Insights Client Configuration in order to be authorized to upload.

    `vim etc/insights-client.conf`
    `auto_config=False`
    `username=<your_username>`
    `password=<your_password>`

**Note:** The username and password is based off your login for https://accesss.redhat.com/

Upload Command:
^^^^^^^^^^^^^^^
To upload a QPC report file using the Insight Clients you will need to run the following command:

    sudo EGG=/etc/insights-client/rpm.egg BYPASS_GPG=True insights-client --no-gpg --payload=test.tar.gz --content-type=application/vnd.redhat.qpc.test+tgz
