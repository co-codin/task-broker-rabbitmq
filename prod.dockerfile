FROM python:3.8-alpine
ARG SERVICE_PORT=8000
RUN pip install --no-cache-dir -U pip

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN RUN mkdir -p /task_broker

WORKDIR /task_broker

RUN mkdir -p /var/logs/
RUN mkdir logs

COPY app/ ./app/

EXPOSE $SERVICE_PORT
CMD ["uvicorn", "app.main:app" , "--host", "0.0.0.0", "--port", "8000"]

#CMD ["uvicorn", "app.main:app" , "--host", "0.0.0.0", "--port", "8000"]
#CMD ["python3","-m","app.main.py"]

