# Generated by Django 4.2.16 on 2024-11-05 19:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('replacing_documents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='installdocumentrequest',
            name='issue_organization',
            field=models.TextField(blank=True, default='Лениградское шоссе, д. 31/2', null=True),
        ),
        migrations.AlterField(
            model_name='installdocumentrequest',
            name='new_client_surname',
            field=models.TextField(blank=True, default='Пятигорская', null=True),
        ),
        migrations.AlterField(
            model_name='installdocumentrequest',
            name='replace_reason',
            field=models.TextField(blank=True, default='Вступление в брак', null=True),
        ),
    ]
