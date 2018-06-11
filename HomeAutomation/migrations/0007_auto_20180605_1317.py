# Generated by Django 2.0.2 on 2018-06-05 16:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HomeAutomation', '0006_auto_20180603_1859'),
    ]

    operations = [
        migrations.CreateModel(
            name='StateVariable',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('type', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=50)),
                ('min', models.IntegerField(default=0)),
                ('max', models.IntegerField(default=1)),
                ('scale', models.IntegerField(default=1)),
                ('artifact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='HomeAutomation.Artifact')),
            ],
        ),
        migrations.RemoveField(
            model_name='booleanvariable',
            name='artifact',
        ),
        migrations.RemoveField(
            model_name='booleanvariable',
            name='polymorphic_ctype',
        ),
        migrations.RemoveField(
            model_name='rangevariable',
            name='artifact',
        ),
        migrations.RemoveField(
            model_name='rangevariable',
            name='polymorphic_ctype',
        ),
        migrations.RemoveField(
            model_name='valuevariable',
            name='artifact',
        ),
        migrations.RemoveField(
            model_name='valuevariable',
            name='polymorphic_ctype',
        ),
        migrations.DeleteModel(
            name='BooleanVariable',
        ),
        migrations.DeleteModel(
            name='RangeVariable',
        ),
        migrations.DeleteModel(
            name='ValueVariable',
        ),
    ]
