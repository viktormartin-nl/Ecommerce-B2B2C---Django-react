# Generated by Django 4.0.6 on 2022-07-13 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0090_alter_check_filter_subject'),
    ]

    operations = [
        migrations.AlterField(
            model_name='check',
            name='filter_body',
            field=models.BooleanField(default=False),
        ),
    ]
