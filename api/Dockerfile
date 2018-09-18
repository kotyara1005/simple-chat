FROM python:3.6-slim

WORKDIR /api

ADD . /api

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8000

ENV NAME Api

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "chat.wsgi"]
