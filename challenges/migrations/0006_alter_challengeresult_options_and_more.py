# Generated by Django 5.1.6 on 2025-04-22 17:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0005_userprofile_losses_userprofile_points_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='challengeresult',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='challengeresult',
            name='challenge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.challenge'),
        ),
    ]
