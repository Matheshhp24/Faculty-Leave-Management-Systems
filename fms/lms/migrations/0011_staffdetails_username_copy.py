# Generated by Django 5.0.6 on 2024-06-12 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0010_rename_announcement_announcement_announcement_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffdetails',
            name='username_copy',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
