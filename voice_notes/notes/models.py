from django.conf import settings
from django.db import models


class Note(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notes'
    )
    course = models.CharField(max_length=100, blank=True)
    text = models.TextField()
    title = models.CharField(max_length=150, blank=True)
    source_filename = models.CharField(max_length=255, blank=True)
    audio_file = models.FileField(upload_to='audio_uploads/', null=True, blank=True)
    transcription_source = models.CharField(max_length=50, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        title = (self.title or self.text[:50]).replace('\n', ' ')
        return f"{self.course or 'General'} Note {self.id}: {title}"


class StudyResource(models.Model):
    STUDENT_NOTE = 'note'
    PAST_PAPER = 'paper'
    RESOURCE_TYPE_CHOICES = [
        (STUDENT_NOTE, 'Student Note'),
        (PAST_PAPER, 'Past Paper'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='resources'
    )
    title = models.CharField(max_length=150)
    course = models.CharField(max_length=100, blank=True)
    exam_board = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    file = models.FileField(upload_to='past_papers/', null=True, blank=True)
    resource_type = models.CharField(
        max_length=10,
        choices=RESOURCE_TYPE_CHOICES,
        default=STUDENT_NOTE,
    )
    year = models.PositiveIntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_resource_type_display()} {self.id}: {self.title}"


class ResourceAnswer(models.Model):
    resource = models.ForeignKey(
        StudyResource,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='resource_answers'
    )
    question_text = models.TextField()
    answer_text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer for {self.resource.title}: {self.question_text[:40].replace('\n', ' ')}"
