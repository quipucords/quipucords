FROM fedora:26

RUN yum -y groupinstall "Development tools"
RUN yum -y install python-devel python-tools python3-devel python3-tools sshpass which

RUN pip install virtualenv
RUN virtualenv -p python3 ~/venv

# Setup dependencies
COPY requirements.txt /tmp/reqs.txt
# Remove last 2 lines
RUN sed -e :a -e '$d;N;2,3ba' -e 'P;D' /tmp/reqs.txt > /tmp/requirements.txt
RUN . ~/venv/bin/activate;pip install -r /tmp/requirements.txt
RUN . ~/venv/bin/activate;pip install coverage==3.6

# Copy server code
COPY . /tmp/
WORKDIR /tmp/


# Initialize database
RUN . ~/venv/bin/activate;python -V;make server-init

EXPOSE 8000
CMD . ~/venv/bin/activate;python -V;python /tmp/quipucords/manage.py runserver 0.0.0.0:8000
