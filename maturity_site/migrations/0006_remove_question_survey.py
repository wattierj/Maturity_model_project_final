# Generated by Django 5.1.6 on 2025-04-03 12:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maturity_site', '0005_alter_dimension_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='survey',
        ),
    ]
