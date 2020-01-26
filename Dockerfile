FROM python:3.7
ENV PYTHONUNBUFFERED 1

#RUN apk update && apk add --virtual build-deps python3-dev
RUN apt-get update && apt-get install -y tesseract-ocr ffmpeg

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 80
WORKDIR /opt/

ENTRYPOINT ["/bin/sh", "/opt/entrypoint.sh"]

