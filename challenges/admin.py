from django.contrib import admin
from .models import DailyChallenge, UserSubmission, ChallengeResult, UserProfile

admin.site.register(DailyChallenge)
admin.site.register(UserSubmission)
admin.site.register(ChallengeResult)
admin.site.register(UserProfile)
