# Generated by Django 5.1.2 on 2024-10-26 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0020_remove_cart_client_cart_session_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryoption',
            name='delivery_description',
            field=models.TextField(blank=True, null=True, verbose_name='Pristatymo aprašymas'),
        ),
    ]
