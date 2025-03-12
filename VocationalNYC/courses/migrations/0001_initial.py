# Generated by Django 5.1.6 on 2025-03-11 14:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                ("course_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("keywords", models.CharField(blank=True, max_length=255, null=True)),
                ("course_desc", models.TextField()),
                ("cost", models.IntegerField(default=0)),
                ("location", models.CharField(max_length=255)),
                ("classroom_hours", models.IntegerField(default=0)),
                ("lab_hours", models.IntegerField(default=0)),
                ("internship_hours", models.IntegerField(default=0)),
                ("practical_hours", models.IntegerField(default=0)),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="course",
                        to="users.provider",
                    ),
                ),
            ],
        ),
    ]
