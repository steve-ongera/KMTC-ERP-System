# Generated by Django 5.2 on 2025-07-25 15:19

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_application', '0002_studentreporting'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='hostel',
            options={'ordering': ['hostel_type', 'name']},
        ),
        migrations.RemoveField(
            model_name='hostel',
            name='capacity',
        ),
        migrations.RemoveField(
            model_name='hostel',
            name='rules_regulations',
        ),
        migrations.RemoveField(
            model_name='hostel',
            name='warden_contact',
        ),
        migrations.RemoveField(
            model_name='hostel',
            name='warden_name',
        ),
        migrations.AddField(
            model_name='hostel',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='hostel',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='hostel',
            name='rules_and_regulations',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hostel',
            name='school',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='hostels', to='core_application.school'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='hostel',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='hostel',
            name='warden',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_hostels', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='hostel',
            name='facilities',
            field=models.TextField(blank=True, help_text='Available facilities like WiFi, laundry, etc.'),
        ),
        migrations.AlterField(
            model_name='hostel',
            name='hostel_type',
            field=models.CharField(choices=[('boys', 'Boys Hostel'), ('girls', 'Girls Hostel')], max_length=10),
        ),
        migrations.AlterField(
            model_name='hostel',
            name='total_rooms',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
