# Generated by Django 5.0.6 on 2024-07-22 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0024_default_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffdetails',
            name='is_principal',
            field=models.BooleanField(default=False),
        ),
    ]
