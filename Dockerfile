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
RUN . ~/venv/bin/activate;pip install gunicorn==19.7.1

# Create /etc/ssl
RUN mkdir -p /etc/ssl/
COPY deploy/ssl/* /etc/ssl/
VOLUME /etc/ssl

# Create /deploy
RUN mkdir -p /deploy
COPY deploy/gunicorn.conf.py  /deploy
COPY deploy/run.sh  /deploy

# Config supervisor
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directories
RUN mkdir -p /var/log/supervisor/
VOLUME /var/log

# Create /sshkeys
RUN mkdir -p /sshkeys
VOLUME /sshkeys

# Create /var/data
RUN mkdir -p /var/data
VOLUME /var/data

# Create /etc/ansible/roles/
RUN mkdir -p /etc/ansible/roles/
COPY roles/ /etc/ansible/roles/
VOLUME /etc/ansible/roles/

# Copy server code
COPY . /app/
WORKDIR /app

# Set production environment
ENV PRODUCTION=True
ENV DJANGO_SECRET_PATH=/var/data/secret.txt
ENV DJANGO_DB_PATH=/var/data/
ENV DJANGO_DEBUG=False
ENV DJANGO_LOG_LEVEL=INFO
ENV DJANGO_LOG_FORMATTER=verbose
ENV DJANGO_LOG_HANDLERS=console,file
ENV DJANGO_LOG_FILE=/var/log/app.log
ENV QUIPUCORDS_LOGGING_LEVEL=INFO
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8

# Initialize database & Collect static files
RUN . ~/venv/bin/activate;make server-init server-static
RUN ls -lta /var/data

WORKDIR /var/log

EXPOSE 443
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
