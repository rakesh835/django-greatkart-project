# Generated by Django 3.2.11 on 2023-02-26 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='landmark',
            field=models.CharField(blank=True, default=None, max_length=50),
            preserve_default=False,
        ),
    ]
