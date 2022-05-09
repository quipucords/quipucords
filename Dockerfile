FROM redhat/ubi8

RUN dnf -yq install python39 make openssh-clients glibc-langpack-en git &&\
    dnf clean all &&\
    python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:${PATH}"

RUN pip install --upgrade pip

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Fetch UI code
COPY Makefile .
ARG UI_RELEASE=0.9.3
RUN make fetch-ui -e QUIPUCORDS_UI_RELEASE=${UI_RELEASE}

# Create /etc/ssl/qpc
COPY deploy/ssl/* /etc/ssl/qpc/

# Create /deploy
COPY deploy/*  /deploy/

# Create log directories
VOLUME /var/log

# Create /var/data
VOLUME /var/data

# Create /etc/ansible/roles/
RUN mkdir -p /etc/ansible/roles/
COPY quipucords/scanner/network/runner/roles/ /etc/ansible/roles/
VOLUME /etc/ansible/roles/

# Copy server code
COPY . .

# Set production environment
ARG BUILD_COMMIT=master
ENV QUIPUCORDS_COMMIT=$BUILD_COMMIT
ENV PRODUCTION=True
ENV DJANGO_SECRET_PATH=/var/data/secret.txt
ENV DJANGO_DB_PATH=/var/data/
ENV DJANGO_DEBUG=False
ENV DJANGO_LOG_LEVEL=INFO
ENV DJANGO_LOG_FORMATTER=verbose
ENV DJANGO_LOG_HANDLERS=console,file
ENV DJANGO_LOG_FILE=/var/log/app.log
ENV QUIPUCORDS_LOG_LEVEL=INFO
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/app/quipucords

# Install quipucords as package
RUN pip install -v -e .

# Collect static files
RUN make server-static

WORKDIR /var/log

EXPOSE 443
CMD ["/bin/bash", "/deploy/docker_run.sh"]