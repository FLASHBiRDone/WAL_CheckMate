FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY .env .
COPY templates templates

RUN mkdir /app/data && chown -R nobody:nogroup /app/data
VOLUME /app/data

ENV TZ=Europe/Oslo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV PYTHONUNBUFFERED=1

EXPOSE 5003

CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "4", "app:app"]