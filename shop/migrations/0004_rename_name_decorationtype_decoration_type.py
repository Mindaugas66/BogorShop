# Generated by Django 5.1.2 on 2024-10-21 08:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_alter_flowers_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='decorationtype',
            old_name='name',
            new_name='decoration_type',
        ),
    ]