FROM apache/airflow:2.8.1

USER root

# Install additional system dependencies if needed
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

    
# Create required directories with proper permissions
RUN mkdir -p /opt/airflow/logs \
    && chown -R airflow:root /opt/airflow

USER airflow

# Set the entrypoint to use the official Airflow entrypoint
ENTRYPOINT ["/usr/bin/dumb-init", "--", "/entrypoint"] 