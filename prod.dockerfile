FROM python:3.8-alpine

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

WORKDIR /task_broker
COPY app/ ./app/

CMD ["uvicorn", "app.main:app" , "--host", "0.0.0.0", "--port", "8000"]