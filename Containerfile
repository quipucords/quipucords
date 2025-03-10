FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:14f14e03d68f7fd5f2b18a13478b6b127c341b346c86b6e0b886ed2b7573b8e0

ARG K8S_DESCRIPTION="Quipucords"
ARG K8S_DISPLAY_NAME="quipucords-server"
ARG K8S_NAME="quipucords/quipucords-server"
ARG OCP_TAGS="quipucords"
ARG REDHAT_COMPONENT="quipucords-container"
ARG QUIPUCORDS_INSIGHTS_DATA_COLLECTOR_LABEL="quipucords"

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
ENV PYTHONPATH=/app/quipucords
ENV QUIPUCORDS_DATA_DIR=/var/data
ENV QUIPUCORDS_LOG_DIRECTORY=/var/log
ENV QUIPUCORDS_LOG_LEVEL=INFO
ENV QUIPUCORDS_PRODUCTION=True
ENV QUIPUCORDS_INSIGHTS_DATA_COLLECTOR_LABEL=${QUIPUCORDS_INSIGHTS_DATA_COLLECTOR_LABEL}

COPY scripts/dnf /usr/local/bin/dnf
ARG BUILD_PACKAGES="crypto-policies-scripts gcc libpq-devel python3.12-devel"
RUN dnf install \
        git \
        glibc-langpack-en \
        jq \
        libpq \
        make \
        nmap-ncat \
        openssh-clients \
        procps-ng \
        python3.12 \
        python3.12-pip \
        sshpass \
        tar \
        which \
        ${BUILD_PACKAGES} \
        -y &&\
    dnf clean all &&\
    python3.12 -m venv /opt/venv

# set cryptographic policy to a mode compatible with older systems (like RHEL5&6)
RUN update-crypto-policies --set LEGACY

RUN pip install --upgrade pip wheel

WORKDIR /app
COPY lockfiles/requirements.txt .
RUN pip install -r requirements.txt
RUN dnf remove ${BUILD_PACKAGES} -y && \
    dnf clean all

# Create /deploy
COPY deploy  /deploy

# Create log directories
VOLUME /var/log

# Create /var/data
RUN mkdir -p /var/data
VOLUME /var/data

# Copy server code
COPY . .

# Install quipucords as package
RUN pip install -v -e .

# Collect static files
RUN make server-static

# Allow git to run in /app
RUN git config --file /.gitconfig --add safe.directory /app

# konflux requires the application license at /licenses
RUN mkdir -p /licenses
COPY LICENSE /licenses/LICENSE
# konflux requires a non-root user
# let's follow software collection tradition and use uid 1001
# https://github.com/sclorg/s2i-base-container/blob/3598eab2/core/Dockerfile#L72
RUN useradd -u 1001 -r -g 0 -d /app -c "Quipucords user" quipucords && \
    chown 1001:0 -R /app /deploy /var /opt/venv /licenses
USER 1001

EXPOSE 8000
CMD ["/bin/bash", "/deploy/entrypoint_web.sh"]

LABEL com.redhat.component=${REDHAT_COMPONENT} \
    description=${K8S_DESCRIPTION} \
    io.k8s.description=${K8S_DESCRIPTION} \
    io.k8s.display-name=${K8S_DISPLAY_NAME} \
    io.openshift.tags=${OCP_TAGS} \
    name=${K8S_NAME} \
    summary=${K8S_DESCRIPTION}
