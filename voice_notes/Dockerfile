FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate --noinput || true

ENV PORT 8000

CMD ["gunicorn", "voice_notes.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
