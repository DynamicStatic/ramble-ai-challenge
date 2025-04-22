from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import requests
from django.conf import settings

class Challenge(models.Model):
    CHALLENGE_TYPES = [
        ('daily', 'Daily Challenge'),
        ('random', 'Random Challenge'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    type = models.CharField(max_length=10, choices=CHALLENGE_TYPES, default='daily')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    @classmethod
    def generate_random_challenge(cls):
        """Generate a random challenge using OpenAI's API"""
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = """Generate a creative and engaging image generation challenge. 
        The challenge should be specific enough to guide users but open enough to allow for creativity.
        Format the response as a JSON object with 'title' and 'description' fields.
        The title should be catchy and the description should be detailed but concise."""
        
        data = {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()['choices'][0]['message']['content']
            # Parse the JSON response
            import json
            challenge_data = json.loads(result)
            
            # Create a new random challenge
            challenge = cls(
                title=challenge_data['title'],
                description=challenge_data['description'],
                type='random',
                end_date=timezone.now() + timezone.timedelta(days=7)  # Random challenges last 7 days
            )
            challenge.save()
            return challenge
            
        except Exception as e:
            print(f"Error generating random challenge: {str(e)}")
            return None

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
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    prompt = models.TextField()
    generated_image = models.ImageField(upload_to='submissions/')
    submission_number = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s submission for {self.challenge.title}"

class ChallengeResult(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    winner = models.ForeignKey(UserSubmission, on_delete=models.CASCADE, related_name='wins')
    loser = models.ForeignKey(UserSubmission, on_delete=models.CASCADE, related_name='losses')
    judge_feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Challenge Result: {self.winner.user.username} vs {self.loser.user.username}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    points = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    
    @property
    def win_rate(self):
        total = self.wins + self.losses
        if total == 0:
            return 0
        return (self.wins / total) * 100
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submission = models.ForeignKey(UserSubmission, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'submission')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} likes {self.submission.user.username}'s submission"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submission = models.ForeignKey(UserSubmission, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.submission.user.username}'s submission"
