FROM python:3.9
ENV PYTHONUNBUFFERED 1

#RUN apk update && apk add --virtual build-deps python3-dev
RUN apt-get update && apt-get install -y libgl1-mesa-glx tesseract-ocr

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8080
WORKDIR /opt/kinksorter

COPY src /opt/kinksorter

RUN chmod +x /opt/kinksorter/entrypoint.sh
ENTRYPOINT ["/opt/kinksorter/entrypoint.sh"]
