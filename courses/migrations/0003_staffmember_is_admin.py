# Generated by Django 4.2.17 on 2025-01-11 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_sectionattempt_attempt_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffmember',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
    ]
