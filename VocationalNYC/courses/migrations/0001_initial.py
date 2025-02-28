# Generated by Django 5.1.6 on 2025-02-25 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('course_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('course_desc', models.TextField()),
                ('time', models.CharField(max_length=100)),
                ('location', models.CharField(max_length=255)),
            ],
        ),
    ]
