# Generated by Django 5.1.2 on 2024-10-21 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_remove_decorationtype_prduct_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='decorationtype',
            name='prduct_image',
            field=models.ImageField(default=None, upload_to='decorations/product/'),
            preserve_default=False,
        ),
    ]