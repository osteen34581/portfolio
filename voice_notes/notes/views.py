import io
import json
import os
import re
import tempfile
import zipfile
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from django.http import FileResponse, JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Note, StudyResource, ResourceAnswer


def index(request):
    course_filter = request.GET.get('course', '').strip()
    query = request.GET.get('q', '').strip()
    resource_year_filter = request.GET.get('resource_year', '').strip()
    exam_board_filter = request.GET.get('exam_board', '').strip()
    resource_type_filter = request.GET.get('resource_type', '').strip()

    notes = Note.objects.order_by('-created')
    if request.user.is_authenticated:
        notes = notes.filter(owner=request.user)
    if course_filter:
        notes = notes.filter(course__icontains=course_filter)
    if query:
        notes = notes.filter(text__icontains=query)
    notes = notes[:50]

    resources = StudyResource.objects.order_by('-created')
    if request.user.is_authenticated:
        resources = resources.filter(models.Q(owner__isnull=True) | models.Q(owner=request.user))
    else:
        resources = resources.filter(owner__isnull=True)

    if course_filter:
        resources = resources.filter(course__icontains=course_filter)
    if query:
        resources = resources.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(content__icontains=query)
        )
    if resource_type_filter in [StudyResource.STUDENT_NOTE, StudyResource.PAST_PAPER]:
        resources = resources.filter(resource_type=resource_type_filter)
    if resource_year_filter:
        resources = resources.filter(year=resource_year_filter)
    if exam_board_filter:
        resources = resources.filter(exam_board__icontains=exam_board_filter)

    student_notes = resources.filter(resource_type=StudyResource.STUDENT_NOTE)[:8]
    past_papers = resources.filter(resource_type=StudyResource.PAST_PAPER)[:8]

    return render(request, 'notes/index.html', {
        'notes': notes,
        'course_filter': course_filter,
        'query': query,
        'resource_year_filter': resource_year_filter,
        'exam_board_filter': exam_board_filter,
        'resource_type_filter': resource_type_filter,
        'student_notes': student_notes,
        'past_papers': past_papers,
    })


def parse_past_paper_questions(content):
    lines = content.replace('\r\n', '\n').split('\n')
    questions = []
    current = None
    for line in lines:
        heading = re.match(r'^\s*(?:Question\s*\d+|Q\s*\d+|\d+[\.)])\s*(.*)', line, re.IGNORECASE)
        if heading:
            if current:
                questions.append(current)
            current = {
                'question': heading.group(0).strip(),
                'content': ''
            }
        elif current:
            current['content'] += line + '\n'
    if current:
        questions.append(current)

    if not questions:
        text = content.strip()
        if text:
            questions = [{'question': 'Past paper content', 'content': text}]
    return questions


def resource_qa(request, resource_id):
    resource = StudyResource.objects.filter(id=resource_id, resource_type=StudyResource.PAST_PAPER).first()
    if not resource or (resource.owner and resource.owner != request.user):
        return HttpResponseForbidden('Access denied')

    if request.method == 'POST':
        question_text = request.POST.get('question_text', '').strip()
        answer_text = request.POST.get('answer_text', '').strip()
        if question_text and answer_text:
            ResourceAnswer.objects.create(
                resource=resource,
                owner=request.user if request.user.is_authenticated else None,
                question_text=question_text,
                answer_text=answer_text,
            )
        return redirect('resource_qa', resource_id=resource.id)

    questions = parse_past_paper_questions(resource.content)
    answers = resource.answers.order_by('-created')
    return render(request, 'notes/resource_qa.html', {
        'resource': resource,
        'questions': questions,
        'answers': answers,
    })


def add_resource(request):
    if request.method != 'POST':
        return redirect('index')

    title = request.POST.get('title', '').strip()
    course = request.POST.get('course', '').strip()
    exam_board = request.POST.get('exam_board', '').strip()
    description = request.POST.get('description', '').strip()
    content = request.POST.get('content', '').strip()
    resource_type = request.POST.get('resource_type', StudyResource.STUDENT_NOTE)
    year = request.POST.get('year', '').strip()
    year_value = int(year) if year.isdigit() else None
    uploaded_file = request.FILES.get('resource_file')

    file_text = ''
    file_instance = None
    if uploaded_file:
        file_instance = uploaded_file
        filename = uploaded_file.name.lower()
        uploaded_file.seek(0)
        if filename.endswith('.txt'):
            try:
                file_text = uploaded_file.read().decode('utf-8', errors='ignore')
            except Exception:
                file_text = ''
            uploaded_file.seek(0)
        elif filename.endswith('.pdf'):
            try:
                import PyPDF2
                uploaded_file.seek(0)
                reader = PyPDF2.PdfReader(uploaded_file)
                file_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
                uploaded_file.seek(0)
            except Exception:
                file_text = ''

    if title and (content or file_text or file_instance):
        owner = request.user if request.user.is_authenticated else None
        StudyResource.objects.create(
            owner=owner,
            title=title,
            course=course,
            exam_board=exam_board,
            description=description,
            content=content or file_text,
            file=file_instance,
            resource_type=resource_type,
            year=year_value,
        )

    return redirect('index')


def download_resource(request, resource_id):
    resource = StudyResource.objects.filter(id=resource_id).first()
    if not resource or (resource.owner and resource.owner != request.user):
        return HttpResponseForbidden('Access denied')

    if resource.file:
        response = FileResponse(resource.file.open('rb'), as_attachment=True, filename=resource.file.name.split('/')[-1])
        return response

    filename = f"{resource.resource_type}_{resource.id}.txt"
    response = HttpResponse(resource.content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_resource_markdown(request, resource_id):
    resource = StudyResource.objects.filter(id=resource_id).first()
    if not resource or (resource.owner and resource.owner != request.user):
        return HttpResponseForbidden('Access denied')

    content_lines = [f"# {resource.title}"]
    if resource.course:
        content_lines.append(f"**Course:** {resource.course}")
    if resource.exam_board:
        content_lines.append(f"**Exam Board:** {resource.exam_board}")
    if resource.year:
        content_lines.append(f"**Year:** {resource.year}")
    content_lines.append('')
    if resource.description:
        content_lines.append(f"**Description:** {resource.description}")
        content_lines.append('')
    if resource.content:
        content_lines.append(resource.content)
    markdown = '\n'.join(content_lines)
    filename = f"resource_{resource.id}.md"
    response = HttpResponse(markdown, content_type='text/markdown')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_resource_zip(request, resource_id):
    resource = StudyResource.objects.filter(id=resource_id).first()
    if not resource or (resource.owner and resource.owner != request.user):
        return HttpResponseForbidden('Access denied')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        metadata = [f"Title: {resource.title}",
                    f"Course: {resource.course or 'N/A'}",
                    f"Exam Board: {resource.exam_board or 'N/A'}",
                    f"Year: {resource.year or 'N/A'}",
                    f"Type: {resource.get_resource_type_display()}",
                    '']
        if resource.description:
            metadata.append(f"Description: {resource.description}")
            metadata.append('')
        if resource.content:
            archive.writestr('resource.md', '\n'.join(['# ' + resource.title, ''] + metadata + [resource.content]))
        else:
            archive.writestr('resource.md', '\n'.join(['# ' + resource.title, ''] + metadata))
        if resource.file:
            resource.file.open('rb')
            archive.writestr(resource.file.name.split('/')[-1], resource.file.read())
            resource.file.close()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="resource_{resource.id}.zip"'
    return response


@csrf_exempt
def transcribe(request):
    """
    Accepts an uploaded audio file and attempts server-side transcription using
    Whisper if available. Returns JSON with the transcribed text or an error.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'No audio file'}, status=400)

    # save to temp file
    with tempfile.NamedTemporaryFile(suffix='.webm') as tmp:
        for chunk in audio.chunks():
            tmp.write(chunk)
        tmp.flush()

        # Make sure ffmpeg is available for whisper. imageio-ffmpeg provides a binary
        # when ffmpeg is not installed globally.
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            os.environ.setdefault('FFMPEG_BINARY', ffmpeg_exe)
            ffmpeg_dir = os.path.dirname(ffmpeg_exe)

            if os.path.basename(ffmpeg_exe) != 'ffmpeg':
                symlink_dir = tempfile.mkdtemp()
                link_path = os.path.join(symlink_dir, 'ffmpeg')
                try:
                    os.symlink(ffmpeg_exe, link_path)
                except FileExistsError:
                    pass
                os.environ['PATH'] = symlink_dir + os.pathsep + os.environ.get('PATH', '')
            else:
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        except Exception:
            pass

        try:
            import whisper
            if not hasattr(whisper, 'load_model'):
                raise ImportError('openai-whisper package not installed; found wrong whisper package')

            model = whisper.load_model('small')
            result = model.transcribe(tmp.name)
            text = result.get('text', '').strip()
        except Exception as e:
            return JsonResponse({'error': 'Transcription backend unavailable', 'details': str(e)}, status=500)

    course = request.POST.get('course', '').strip()
    owner = request.user if request.user.is_authenticated else None
    note = Note.objects.create(owner=owner, course=course, text=text)
    return JsonResponse({'text': text, 'id': note.id, 'course': course})


def export_text(request, note_id):
    note = Note.objects.filter(id=note_id).first()
    if not note or (note.owner and note.owner != request.user):
        return HttpResponseForbidden('Access denied')
    filename = f"note_{note.id}.txt"
    response = HttpResponse(note.text, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_pdf(request, note_id):
    note = Note.objects.filter(id=note_id).first()
    if not note or (note.owner and note.owner != request.user):
        return HttpResponseForbidden('Access denied')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="note_{note.id}.pdf"'
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    p.setFont('Helvetica-Bold', 14)
    p.drawString(40, height - 40, note.course or 'General')
    p.setFont('Helvetica', 12)
    p.drawString(40, height - 60, note.created.strftime('%Y-%m-%d %H:%M'))
    textobject = p.beginText(40, height - 100)
    textobject.setFont('Helvetica', 11)
    for line in note.text.splitlines():
        textobject.textLine(line)
    p.drawText(textobject)
    p.showPage()
    p.save()
    return response


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@csrf_exempt
def save_text(request):
    """
    Accepts JSON with a `text` field and saves it as a Note. This endpoint is
    used by the client-side (Web Speech API) fallback so the app works without
    Whisper or heavy server deps.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        text = payload.get('text', '').strip()
        course = payload.get('course', '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not text:
        return JsonResponse({'error': 'Empty text'}, status=400)

    owner = request.user if request.user.is_authenticated else None
    note = Note.objects.create(owner=owner, course=course, text=text)
    return JsonResponse({'id': note.id, 'text': note.text, 'course': note.course})
