FROM debian:bookworm-slim

# Install cURL
RUN apt-get update && apt-get install -y \
  curl \
  && rm -rf /var/lib/apt/lists/*

# cURL the latest local development binary
RUN curl https://oso-local-development-binary.s3.amazonaws.com/latest/oso-local-development-binary-linux-x86_64.tar.gz --output local.tar.gz \
  && tar -xzf local.tar.gz \
  && rm local.tar.gz

RUN chmod +x ./standalone

CMD ["./standalone"]
