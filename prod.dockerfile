FROM repo.n3zdrav.ru:18444/python:3.8-alpine
RUN apk add build-base libffi-dev --no-cache
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app/ /app/app/

WORKDIR /app
CMD ["python3", "-m", "app"]
