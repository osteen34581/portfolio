# Voice Notes (Django)

Simple voice-to-text note taker using Django and Whisper.

Setup

1. Create a virtual environment and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Install `ffmpeg` on your system (required by Whisper):

```bash
sudo apt update && sudo apt install ffmpeg -y
```

3. Run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

4. Open http://127.0.0.1:8000/ in your browser and allow microphone.

Notes

- The transcription uses OpenAI's Whisper Python package. Models are downloaded on first use.
- If you prefer a different transcription backend, update `notes/views.py`.
