# Generated by Django 3.0.4 on 2020-06-02 07:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0070_auto_20200411_1310"),
    ]

    operations = [
        migrations.AddField(
            model_name="check",
            name="manual_resume",
            field=models.NullBooleanField(default=False),
        ),
    ]
