FROM python:3.8

RUN pip install --no-cache-dir -U pip

COPY requirements.txt /tmp/
COPY requirements.dev.txt /tmp/
RUN pip install -r /tmp/requirements.txt
RUN pip install -r /tmp/requirements.dev.txt

CMD ["bash"]
