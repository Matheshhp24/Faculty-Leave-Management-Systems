# Generated by Django 5.0.6 on 2024-08-24 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0034_permission_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='leave_availability',
            name='initial_permission_remaining',
            field=models.CharField(default=0, max_length=50),
        ),
        migrations.AddField(
            model_name='leave_availability',
            name='permission_remaining',
            field=models.CharField(default=0, max_length=50),
        ),
    ]
