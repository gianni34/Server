# Generated by Django 2.0.1 on 2018-05-01 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HomeAutomation', '0002_modetype_variable'),
    ]

    operations = [
        migrations.AddField(
            model_name='variable',
            name='max',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='variable',
            name='min',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='variable',
            name='scale',
            field=models.IntegerField(default=1),
        ),
    ]
