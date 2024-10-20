# Generated by Django 5.0.6 on 2024-08-14 03:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0030_frozendates_delete_frozendate'),
    ]

    operations = [
        migrations.CreateModel(
            name='CancelLeave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_type', models.CharField(max_length=100)),
                ('unique_id', models.CharField(max_length=100)),
                ('reason', models.CharField(max_length=500)),
                ('document', models.FileField(blank=True, null=True, upload_to='cancellation_documents/')),
            ],
        ),
    ]
