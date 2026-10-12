FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app/voice_notes

COPY voice_notes/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY voice_notes/ .

RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate --noinput || true

CMD ["gunicorn", "voice_notes.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
