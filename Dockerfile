FROM python:3.7
ENV PYTHONUNBUFFERED 1

#RUN apk update && apk add --virtual build-deps python3-dev

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8080
WORKDIR /opt/kinksorter

COPY src /opt/kinksorter


ENTRYPOINT ["/bin/sh", "/opt/kinksorter/entrypoint.sh"]
