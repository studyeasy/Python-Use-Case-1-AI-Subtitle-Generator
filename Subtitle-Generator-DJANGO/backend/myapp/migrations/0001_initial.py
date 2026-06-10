from django.db import migrations, models

import myapp.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=myapp.models._new_id,
                        editable=False,
                        max_length=36,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("user_sub", models.CharField(db_index=True, max_length=128)),
                ("original_filename", models.CharField(max_length=512)),
                ("language", models.CharField(blank=True, max_length=16, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("QUEUED", "Queued"),
                            ("TRANSCRIBING", "Transcribing"),
                            ("COMPLETED", "Completed"),
                            ("FAILED", "Failed"),
                        ],
                        default="PENDING",
                        max_length=32,
                    ),
                ),
                ("progress", models.IntegerField(default=0)),
                ("error", models.TextField(blank=True, null=True)),
                ("source_key", models.CharField(max_length=1024)),
                ("srt_key", models.CharField(blank=True, max_length=1024, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
