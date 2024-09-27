# Generated by Django 5.0.6 on 2024-08-24 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0033_leave_availability_initial_maternity_leave_remaining_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('username', models.CharField(max_length=50)),
                ('leave_type', models.CharField(default='Maternity Leave', max_length=50)),
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
        migrations.AlterField(
            model_name='leave_availability',
            name='maternity_leave_remaining',
            field=models.CharField(default=60, max_length=50),
        ),
        migrations.AlterField(
            model_name='maternityleave',
            name='leave_type',
            field=models.CharField(default='Maternity Leave', max_length=50),
        ),
    ]
