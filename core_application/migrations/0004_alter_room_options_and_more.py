# Generated by Django 5.2 on 2025-07-25 15:23

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_application', '0003_alter_hostel_options_remove_hostel_capacity_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='room',
            options={'ordering': ['hostel', 'floor', 'room_number']},
        ),
        migrations.RenameField(
            model_name='room',
            old_name='is_available',
            new_name='is_active',
        ),
        migrations.RemoveField(
            model_name='room',
            name='monthly_rent',
        ),
        migrations.RemoveField(
            model_name='room',
            name='room_type',
        ),
        migrations.AddField(
            model_name='room',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='room',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='room',
            name='capacity',
            field=models.IntegerField(default=4, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(8)]),
        ),
        migrations.AlterField(
            model_name='room',
            name='facilities',
            field=models.TextField(blank=True, help_text='Room-specific facilities'),
        ),
        migrations.AlterField(
            model_name='room',
            name='floor',
            field=models.IntegerField(help_text='Floor number (0 for ground floor)', validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='room',
            name='room_number',
            field=models.CharField(max_length=10),
        ),
    ]
