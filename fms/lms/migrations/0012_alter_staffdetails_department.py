# Generated by Django 5.0.6 on 2024-06-13 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0011_staffdetails_username_copy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffdetails',
            name='department',
            field=models.CharField(choices=[('ECE', 'Electronics and Communication Engineering'), ('CSE', 'Computer Science and Engineering'), ('MECH', 'Mechanical Engineering')], max_length=100),
        ),
    ]
