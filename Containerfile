FROM quay.io/konflux-ci/yq@sha256:ff08fe74188fbadf23ce6b2e4d1db8cadd170203214031d093ff4e4e574a45d6 as yq
FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:bafd57451de2daa71ed301b277d49bd120b474ed438367f087eac0b885a668dc
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

# Point to the default path used by cachi2-playground. For koflux this is /cachi2/output/deps/generic/
ARG CRATES_PATH="/tmp/output/deps/generic"
COPY --from=yq /usr/bin/yq /usr/bin/yq
COPY scripts/dnf /usr/local/bin/dnf
COPY rpms.in.yaml rpms.in.yaml
# distinguish RUNTIME and BUILD dependencies so the latter can be removed later
RUN RUNTIME_DEPS=$(yq '.packages' rpms.in.yaml | grep '# runtime dependencies' -A10000 | yq 'join(" ")') &&\
    BUILD_DEPS=$(yq '.packages' rpms.in.yaml | grep '# runtime dependencies' -B10000 | yq 'join(" ")') &&\
    dnf install ${RUNTIME_DEPS} -y &&\
    rpm -qa > runtime_deps.txt &&\
    dnf install ${BUILD_DEPS} -y &&\
    rpm -qa > all_deps.txt &&\
    dnf clean all &&\
    python3.12 -m venv /opt/venv

# TODO remove prepare_rust_deps script when cachi2/hermeto supports pip+cargo dependencies 
COPY scripts/prepare_rust_deps.py .
RUN python prepare_rust_deps.py "${CRATES_PATH}"

COPY lockfiles/requirements.txt .
RUN pip install -r requirements.txt

# set cryptographic policy to a mode compatible with older systems (like RHEL5&6)
RUN update-crypto-policies --set LEGACY

# remove build dependencies and unecessary build files
RUN dnf remove $(comm -13 runtime_deps.txt all_deps.txt) -y && \
    dnf clean all &&\
    rm -rf /usr/local/bin/yq /usr/local/bin/dnf rpms.in.yaml requirements.txt *_deps.txt

# Allow git to run in /app
RUN git config --file /.gitconfig --add safe.directory /app

# Create /deploy
COPY deploy  /deploy

# Create log directories
VOLUME /var/log

# Create /var/data
RUN mkdir -p /var/data
VOLUME /var/data

# konflux requires the application license at /licenses
RUN mkdir -p /licenses
COPY LICENSE /licenses/LICENSE

# konflux requires a non-root user
# let's follow software collection tradition and use uid 1001
# https://github.com/sclorg/s2i-base-container/blob/3598eab2/core/Dockerfile#L72
RUN useradd -u 1001 -r -g 0 -d /app -c "Quipucords user" quipucords && \
    chown 1001:0 -R /deploy /var /opt/venv /licenses

WORKDIR /app

# Copy server code
COPY . .

# Install quipucords as package
RUN pip install -e .

# Collect static files
RUN make server-static

# also set the ownership in /app and finally change to 1001 user
RUN chown 1001:0 -R /app
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
