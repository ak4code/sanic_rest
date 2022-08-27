FROM python:3.10.5

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install -U setuptools pip

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .