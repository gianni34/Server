# Generated by Django 2.0.1 on 2018-07-18 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HomeAutomation', '0011_auto_20180707_2327'),
    ]

    operations = [
        migrations.RenameField(
            model_name='artifact',
            old_name='power',
            new_name='on',
        ),
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        migrations.AddField(
            model_name='user',
            name='isAdmin',
            field=models.BooleanField(default=False),
        ),
    ]