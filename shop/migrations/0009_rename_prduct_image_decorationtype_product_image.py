# Generated by Django 5.1.2 on 2024-10-21 16:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_decorationtype_prduct_image'),
    ]

    operations = [
        migrations.RenameField(
            model_name='decorationtype',
            old_name='prduct_image',
            new_name='product_image',
        ),
    ]