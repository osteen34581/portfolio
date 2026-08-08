from celery import shared_task
import os
import traceback
from django.conf import settings
from .models import Note

@shared_task
def process_audio_task(note_id):
    """Background task: transcode the Note.audio_file to WAV (if needed), run
    Whisper transcription, and save the text back onto the Note.
    """
    try:
        note = Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return {'error': 'note not found'}

    audio_path = None
    if not note.audio_file:
        note.transcription_source = 'error'
        note.save()
        return {'error': 'no audio file on note'}

    audio_path = note.audio_file.path

    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = None

    transcribe_path = audio_path
    if ffmpeg_exe and not audio_path.lower().endswith(('.wav', '.wave')):
        try:
            wav_tmp = audio_path + '.transcoded.wav'
            import subprocess
            subprocess.run([ffmpeg_exe, '-y', '-i', audio_path, wav_tmp], check=True)
            transcribe_path = wav_tmp
        except Exception:
            transcribe_path = audio_path

    try:
        import whisper
        model = whisper.load_model('small')
        result = model.transcribe(transcribe_path)
        text = result.get('text', '').strip()
        note.text = text
        note.transcription_source = 'whisper'
        note.save()
    except Exception as e:
        note.transcription_source = 'error'
        note.save()
        return {'error': str(e), 'traceback': traceback.format_exc()}

    # cleanup temporary transcode if created
    try:
        if 'wav_tmp' in locals() and os.path.exists(wav_tmp):
            os.unlink(wav_tmp)
    except Exception:
        pass

    return {'ok': True, 'note_id': note.id}
