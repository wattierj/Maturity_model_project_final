# Generated by Django 5.1.6 on 2025-04-10 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maturity_site', '0007_alter_question_axe'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_identification',
            field=models.BooleanField(blank=True, default=False, help_text='Not usable question in the sum of maturity level', null=True),
        ),
    ]
