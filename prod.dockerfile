FROM python:3.8-alpine
ARG SERVICE_PORT=8000
RUN pip install --no-cache-dir -U pip
RUN apk add build-base libffi-dev
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY app/ /app/app/

EXPOSE $SERVICE_PORT

WORKDIR /app
CMD ["python3", "-m", "app"]
