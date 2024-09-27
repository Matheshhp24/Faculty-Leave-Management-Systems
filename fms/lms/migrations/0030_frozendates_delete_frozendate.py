# Generated by Django 5.0.6 on 2024-08-13 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0029_default_table_frozendate_staffdepartment_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FrozenDates',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dates_and_reasons', models.JSONField(default=dict)),
            ],
        ),
        migrations.DeleteModel(
            name='FrozenDate',
        ),
    ]
