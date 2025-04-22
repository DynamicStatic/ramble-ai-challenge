from django import forms
from .models import UserProfile, Challenge

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']

class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ['title', 'description', 'end_date']
        widgets = {
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        } 