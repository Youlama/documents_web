# Generated by Django 4.2.16 on 2024-11-06 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('replacing_documents', '0002_alter_installdocumentrequest_issue_organization_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='installdocumentrequest',
            name='issue_organization',
        ),
        migrations.AddField(
            model_name='documentinrequest',
            name='issue_organization',
            field=models.TextField(blank=True, default='Лениградское шоссе, д. 31/2', null=True),
        ),
    ]
