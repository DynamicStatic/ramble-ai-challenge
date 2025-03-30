from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class DailyChallenge(models.Model):
    CATEGORY_CHOICES = [
        ('character', 'Character Design'),
        ('landscape', 'Landscapes'),
        ('abstract', 'Abstract Art'),
        ('concept', 'Concept Art'),
        ('portrait', 'Portraits'),
        ('scifi', 'Sci-Fi'),
        ('fantasy', 'Fantasy'),
        ('anime', 'Anime Style'),
        ('realistic', 'Realistic'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other'
    )

    def __str__(self):
        return f"Challenge for {self.date}"

    class Meta:
        ordering = ['-date']

class UserSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE)
    prompt = models.TextField()
    generated_image = models.ImageField(upload_to='submissions/')
    submission_number = models.IntegerField(default=1)  # Track which submission this is for the user
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s submission for {self.challenge.date}"

class ChallengeResult(models.Model):
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE)
    winner = models.ForeignKey(UserSubmission, on_delete=models.CASCADE, related_name='wins')
    loser = models.ForeignKey(UserSubmission, on_delete=models.CASCADE, related_name='losses')
    judge_feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Challenge Result: {self.challenge.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    about_me = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    instagram_handle = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
