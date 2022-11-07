FROM python:3.8-alpine

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY app/ /app/
WORKDIR /app

CMD ["uvicorn", "main:app" , "--host", "0.0.0.0", "--port", "80"]
