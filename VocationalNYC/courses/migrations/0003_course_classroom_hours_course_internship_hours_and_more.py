# Generated by Django 5.1.6 on 2025-03-11 04:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0002_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="classroom_hours",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="course",
            name="internship_hours",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="course",
            name="lab_hours",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="course",
            name="practical_hours",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="course",
            name="provider",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="course",
                to="users.provider",
            ),
        ),
        migrations.DeleteModel(
            name="CourseDuration",
        ),
    ]
