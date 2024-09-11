# start with a minimal image
FROM debian:bookworm-slim

# get base dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# create the runtime environment for the app
RUN useradd -ms /bin/bash app
RUN mkdir -p /app && chown app:app /app

# create data directory
RUN mkdir -p /data && chown app:app /data

USER app
WORKDIR /app

# fetch the pinned local development binary
RUN curl https://oso-local-development-binary.s3.amazonaws.com/1.8.4/oso-local-development-binary-linux-x86_64.tar.gz --output local.tar.gz \
  && tar -xzf local.tar.gz \
  && rm local.tar.gz

RUN chmod +x ./standalone

ENV OSO_DIRECTORY=/data
ENV OSO_PORT=8081
ENV OSO_FEATURES="reconcile-facts-update"

ENTRYPOINT ["/app/standalone", "--watch-for-changes", "/policy/policy.polar"]
