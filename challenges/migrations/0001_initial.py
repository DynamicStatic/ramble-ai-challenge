# Generated by Django 5.1.7 on 2025-03-30 18:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyChallenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('date', models.DateField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('category', models.CharField(choices=[('character', 'Character Design'), ('landscape', 'Landscapes'), ('abstract', 'Abstract Art'), ('concept', 'Concept Art'), ('portrait', 'Portraits'), ('scifi', 'Sci-Fi'), ('fantasy', 'Fantasy'), ('anime', 'Anime Style'), ('realistic', 'Realistic'), ('other', 'Other')], default='other', max_length=20)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField(default=0)),
                ('wins', models.IntegerField(default=0)),
                ('losses', models.IntegerField(default=0)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('about_me', models.TextField(blank=True, max_length=500)),
                ('location', models.CharField(blank=True, max_length=100)),
                ('website', models.URLField(blank=True)),
                ('twitter_handle', models.CharField(blank=True, max_length=50)),
                ('instagram_handle', models.CharField(blank=True, max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt', models.TextField()),
                ('generated_image', models.ImageField(upload_to='submissions/')),
                ('submission_number', models.IntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.dailychallenge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChallengeResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('judge_feedback', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.dailychallenge')),
                ('loser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='losses', to='challenges.usersubmission')),
                ('winner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wins', to='challenges.usersubmission')),
            ],
        ),
    ]
