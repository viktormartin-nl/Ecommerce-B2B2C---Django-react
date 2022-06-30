# Generated by Django 4.0.4 on 2022-05-31 12:11

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0085_ping_object_size'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='check',
            name='last_ping_was_fail',
        ),
        migrations.AlterField(
            model_name='channel',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='check',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='notification',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]