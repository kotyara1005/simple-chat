FROM python:3.6-slim

WORKDIR /api

ADD . /api

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8000

ENV NAME Api

CMD ["./wait-for-it.sh", "rabbit:5672", "-s", "-t", "30", "--", "./wait-for-it.sh", "chat_postgres:5432", "-s", "-t", "30", "--", "gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "chat.wsgi"]
