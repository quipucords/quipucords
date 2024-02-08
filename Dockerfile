FROM registry.access.redhat.com/ubi9/ubi-minimal

ENV DJANGO_DB_PATH=/var/data/
ENV DJANGO_DEBUG=False
ENV DJANGO_LOG_FILE=/var/log/app.log
ENV DJANGO_LOG_FORMATTER=verbose
ENV DJANGO_LOG_HANDLERS=console,file
ENV DJANGO_LOG_LEVEL=INFO
ENV DJANGO_SECRET_PATH=/var/data/secret.txt
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PATH="/opt/venv/bin:${PATH}"
ENV PRODUCTION=True
ENV PYTHONPATH=/app/quipucords
ENV QUIPUCORDS_LOG_LEVEL=INFO
ENV QPC_LOG_DIRECTORY=/var/log

COPY scripts/dnf /usr/local/bin/dnf
ARG BUILD_PACKAGES="crypto-policies-scripts gcc libpq-devel python3.11-devel"
RUN dnf install \
    git \
    glibc-langpack-en \
    jq \
    libpq \
    make \
    openssh-clients \
    procps-ng \
    python3.11 \
    python3.11-pip \
    shadow-utils \
    sshpass \
    tar \
    which \
    ${BUILD_PACKAGES} \
    -y &&\
    dnf clean all &&\
    python3.11 -m venv /opt/venv

# set cryptographic policy to a mode compatible with older systems (like RHEL5&6)
RUN update-crypto-policies --set LEGACY

RUN pip install --upgrade pip wheel

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN dnf remove ${BUILD_PACKAGES} -y && \
    dnf clean all
RUN useradd -M -s /bin/bash -d /app quipucords

# Fetch UI code
COPY Makefile .
ARG UI_RELEASE="latest"
RUN --mount=type=secret,id=gh_api_token make fetch-ui -e QUIPUCORDS_UI_RELEASE=${UI_RELEASE}

# Create /etc/ssl/qpc
COPY deploy/ssl /etc/ssl/qpc

# Create /deploy
COPY deploy  /deploy

# Create log directories
RUN mkdir -p /var/log && chown -R quipucords /var/log
VOLUME /var/log

# Create /var/data
RUN mkdir -p /var/data && chown -R quipucords /var/data
VOLUME /var/data

# Copy server code
COPY . .

# Install quipucords as package
RUN pip install -v -e .

# Make the app run as the quipucords user
RUN chown -R quipucords /app
USER quipucords

# Collect static files
RUN make server-static

# Allow git to run in /app
RUN git config --file /app/.gitconfig --add safe.directory /app

EXPOSE 8000
CMD ["/bin/bash", "/deploy/entrypoint_web.sh"]
