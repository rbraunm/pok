FROM python:3.13-slim

RUN groupadd -g 1000 eqemu \
 && useradd -r -u 1000 -g eqemu eqemu

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN chown -R eqemu:eqemu /app
USER eqemu

CMD ["gunicorn", "--chdir", "/app/web", "--bind", "0.0.0.0:5000", "app:app"]
