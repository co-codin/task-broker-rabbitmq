FROM python:3.10

RUN pip3 install --no-cache-dir -U pip

COPY requirements.txt /tmp/
COPY requirements.dev.txt /tmp/
RUN pip3 install -r /tmp/requirements.dev.txt

WORKDIR /app
CMD ["python", "-m", "app"]
