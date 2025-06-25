FROM quay.io/konflux-ci/yq@sha256:15d0238843d954ee78c9c190705eb8b36f6e52c31434183c37d99a80841a635a as yq
# builder and the "final" stages (and any stage that install rpms) MUST be compatible and derived from
# the same ubi base (for instance, don't use a ubi8 "builder" stage with a "final" ubi9)
FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:e12131db2e2b6572613589a94b7f615d4ac89d94f859dad05908aeb478fb090f as builder
# Point to the default path used by cachi2-playground. For koflux this is /cachi2/output/deps/generic/
ARG CRATES_PATH="/tmp/output/deps/generic"
ENV PATH="/opt/venv/bin:${PATH}"
COPY --from=yq /usr/bin/yq /usr/bin/yq
COPY scripts/dnf /usr/local/bin/dnf
COPY rpms.in.yaml rpms.in.yaml
RUN RPMS=$(yq '.packages | join(" ")' rpms.in.yaml) &&\
    dnf install ${RPMS} -y &&\
    dnf clean all &&\
    python3.12 -m venv /opt/venv

COPY lockfiles/requirements.txt .
RUN pip install -r requirements.txt

FROM registry.access.redhat.com/ubi9/ubi-minimal@sha256:e12131db2e2b6572613589a94b7f615d4ac89d94f859dad05908aeb478fb090f
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

WORKDIR /app
COPY scripts/dnf /usr/local/bin/dnf
COPY --from=yq /usr/bin/yq /usr/local/bin/yq
COPY rpms.in.yaml .
ARG BUILD_DEPS="crypto-policies-scripts"
RUN DEPS=$(yq '.packages' rpms.in.yaml | grep '# runtime dependencies' -A1000 | yq 'join(" ")') &&\
    dnf install ${DEPS} ${BUILD_DEPS} -y &&\
    dnf clean all
# set cryptographic policy to a mode compatible with older systems (like RHEL5&6)
RUN update-crypto-policies --set LEGACY
# cleanup unecessary 
RUN dnf remove ${BUILD_DEPS} -y && \
    dnf clean all &&\
    rm -rf /usr/local/bin/yq /usr/local/bin/dnf

# Create /deploy
COPY deploy  /deploy

# Create log directories
VOLUME /var/log

# Create /var/data
RUN mkdir -p /var/data
VOLUME /var/data

# copy virtual env prepared on builder layer
COPY --from=builder /opt/venv /opt/venv

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
