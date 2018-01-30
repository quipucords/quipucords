FROM fedora:26

RUN yum -y groupinstall "Development tools"
RUN yum -y install python-devel python-tools python3-devel python3-tools sshpass which supervisor

RUN pip install virtualenv
RUN virtualenv -p python3 ~/venv

# Create base directory
RUN mkdir -p /app

# Setup dependencies
COPY requirements.txt /app/reqs.txt
# Remove last 2 lines
RUN sed -e :a -e '$d;N;2,3ba' -e 'P;D' /app/reqs.txt > /app/requirements.txt
RUN . ~/venv/bin/activate;pip install -r /app/requirements.txt
RUN . ~/venv/bin/activate;pip install coverage==3.6
RUN . ~/venv/bin/activate;pip install gunicorn==19.7.1

# Create /deploy
RUN mkdir -p /deploy
COPY deploy/gunicorn.conf.py  /deploy
COPY deploy/run.sh  /deploy

# Create /etc/ssl
RUN mkdir -p /etc/ssl/
COPY deploy/ssl/* /etc/ssl/
VOLUME /etc/ssl

# Create /var/logs
RUN mkdir -p /var/logs
VOLUME /var/logs

# Copy server code
COPY . /app/
WORKDIR /app/

# Initialize database & Collect static files
RUN . ~/venv/bin/activate;make server-init server-static

WORKDIR /app/quipucords

ENV DJANGO_LOG_LEVEL=INFO
ENV DJANGO_LOG_FORMATTER=verbose
ENV DJANGO_LOG_HANDLERS=console,file
ENV DJANGO_LOG_FILE=/var/logs/app.log

EXPOSE 443
CMD /deploy/run.sh
