FROM python:3.6

# Add sshpass
RUN apt-get update && apt-get install -y sshpass

# Setup dependencies
COPY requirements.txt /tmp/reqs.txt
# Remove last 2 lines
RUN sed -e :a -e '$d;N;2,3ba' -e 'P;D' /tmp/reqs.txt > /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN pip install coverage==3.6

# Copy server code
COPY . /tmp/
WORKDIR /tmp/

# Initialize database
RUN make server-init

EXPOSE 8000
CMD python /tmp/quipucords/manage.py runserver 0.0.0.0:8000
