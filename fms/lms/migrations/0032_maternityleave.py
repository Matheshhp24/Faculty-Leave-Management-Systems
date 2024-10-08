# Generated by Django 5.0.6 on 2024-08-15 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0031_cancelleave'),
    ]

    operations = [
        migrations.CreateModel(
            name='maternityLeave',
            fields=[
                ('username', models.CharField(max_length=50)),
                ('leave_type', models.CharField(default='Onduty', max_length=50)),
                ('date_Applied', models.DateTimeField(max_length=50)),
                ('from_Date', models.CharField(max_length=50)),
                ('to_Date', models.CharField(max_length=50)),
                ('session', models.CharField(max_length=50)),
                ('remaining', models.CharField(default='-', max_length=50)),
                ('total_leave', models.FloatField(default=0)),
                ('status', models.CharField(default='Reviewing', max_length=50)),
                ('unique_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('reason', models.CharField(default='-', max_length=200)),
                ('document', models.FileField(upload_to='leave_documents/')),
            ],
        ),
    ]
