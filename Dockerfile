# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

# tzdata so ZoneInfo('America/Phoenix') works; ca-certs for HTTPS
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 eqemu \
 && useradd -r -u 1000 -g eqemu -d /app eqemu

WORKDIR /app

COPY --chown=eqemu:eqemu requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=eqemu:eqemu app ./web/
COPY --chown=eqemu:eqemu --chmod=0755 entrypoint.sh /app/entrypoint.sh

USER eqemu
ENTRYPOINT ["/app/entrypoint.sh"]
