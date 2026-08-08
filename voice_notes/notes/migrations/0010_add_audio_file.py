from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0009_add_note_text_column'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='audio_file',
            field=models.FileField(upload_to='audio_uploads/', null=True, blank=True),
        ),
    ]
