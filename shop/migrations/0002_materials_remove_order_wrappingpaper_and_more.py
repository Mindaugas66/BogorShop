# Generated by Django 5.1.2 on 2024-10-18 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Materials',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Color')),
                ('remaining', models.FloatField(default=0, verbose_name='Remaining')),
                ('price', models.DecimalField(decimal_places=2, default=0.25, max_digits=10, verbose_name='Price')),
            ],
        ),
        migrations.RemoveField(
            model_name='order',
            name='wrappingpaper',
        ),
        migrations.AddField(
            model_name='decorations',
            name='remaining',
            field=models.IntegerField(default=0, verbose_name='Remaining'),
        ),
        migrations.DeleteModel(
            name='WrappingPaper',
        ),
    ]