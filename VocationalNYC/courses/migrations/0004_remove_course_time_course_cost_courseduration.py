# Generated by Django 5.1.6 on 2025-03-03 16:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_course_keywords'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='time',
        ),
        migrations.AddField(
            model_name='course',
            name='cost',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='CourseDuration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('classroom_hours', models.IntegerField()),
                ('lab_hours', models.IntegerField()),
                ('internship_hours', models.IntegerField()),
                ('practical_hours', models.IntegerField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course')),
            ],
        ),
    ]
