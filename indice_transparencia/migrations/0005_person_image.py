# Generated by Django 2.1.4 on 2019-01-10 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indice_transparencia', '0004_person_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='profile_images/%Y/%m/%d/', verbose_name='Foto para tu perfil'),
        ),
    ]