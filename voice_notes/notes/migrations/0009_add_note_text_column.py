from django.db import migrations


def add_text_column(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(notes_note);")
    columns = [row[1] for row in cursor.fetchall()]
    if 'text' not in columns:
        cursor.execute("ALTER TABLE notes_note ADD COLUMN text TEXT NOT NULL DEFAULT '';")


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0008_remove_note_text_note_source_filename_note_title_and_more'),
    ]

    operations = [
        migrations.RunPython(add_text_column, migrations.RunPython.noop),
    ]
