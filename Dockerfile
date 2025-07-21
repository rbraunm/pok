FROM python:3.13-slim

RUN groupadd -g 1000 eqemu \
 && useradd -r -u 1000 -g eqemu eqemu

WORKDIR /app

COPY app ./web/
COPY requirements.txt ./
COPY entrypoint.sh ./

RUN chown -R eqemu:eqemu /app
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x ./entrypoint.sh

USER eqemu

ENV POK_DEBUG=false
ENV PYTHONPATH=/app/web

ENTRYPOINT ["./entrypoint.sh"]

