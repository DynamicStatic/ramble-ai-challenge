from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from .models import DailyChallenge, UserSubmission, ChallengeResult, UserProfile
from openai import OpenAI
import os
from django.conf import settings
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .forms import UserProfileForm
from django.db.models import Count

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    # Add Bootstrap classes to form fields
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    
    return render(request, 'challenges/register.html', {'form': form})

def home(request):
    # Get active challenge
    challenge = DailyChallenge.objects.filter(is_active=True).first()
    
    # Get submissions
    submissions = UserSubmission.objects.select_related('user', 'challenge').order_by('-created_at')[:10]
    
    # Get prior challenges
    prior_challenges = DailyChallenge.objects.filter(is_active=False).order_by('-date')[:10]
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
        'prior_challenges': prior_challenges,
    }
    return render(request, 'challenges/home.html', context)

@login_required
def submit_challenge(request):
    today = timezone.now().date()
    current_challenge = DailyChallenge.objects.filter(date=today, is_active=True).first()
    
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        if not prompt:
            messages.error(request, 'Please provide a prompt')
            return redirect('submit_challenge')
        
        try:
            # Get the next submission number for this user and challenge
            last_submission = UserSubmission.objects.filter(
                user=request.user,
                challenge=current_challenge
            ).order_by('-submission_number').first()
            
            next_submission_number = (last_submission.submission_number + 1) if last_submission else 1
            
            # Generate image using OpenAI API
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Get the image URL
            image_url = response.data[0].url
            
            # Download the image
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # Generate a filename
            filename = f"submissions/{request.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # Save the image to media storage
            image_path = default_storage.save(filename, ContentFile(img_response.content))
            
            # Create submission with the local image path
            submission = UserSubmission.objects.create(
                user=request.user,
                challenge=current_challenge,
                prompt=prompt,
                generated_image=image_path,
                submission_number=next_submission_number
            )
            
            messages.success(request, 'Your submission has been created!')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f'Error generating image: {str(e)}')
            return redirect('submit_challenge')
    
    return render(request, 'challenges/submit.html', {'challenge': current_challenge})

@login_required
def challenge_user(request, submission_id):
    submission = get_object_or_404(UserSubmission, id=submission_id)
    user_submission = UserSubmission.objects.filter(
        user=request.user,
        challenge=submission.challenge
    ).first()
    
    if not user_submission:
        messages.error(request, 'You need to submit an image first')
        return redirect('submit_challenge')
    
    # Check if user has already challenged this submission
    existing_challenge = ChallengeResult.objects.filter(
        challenge=submission.challenge,
        winner__user__in=[request.user, submission.user],
        loser__user__in=[request.user, submission.user]
    ).exists()
    
    if existing_challenge:
        messages.warning(request, 'You have already challenged this submission!')
        return redirect('view_challenge', challenge_id=submission.challenge.id)
    
    if request.method == 'POST':
        # Use AI to judge the submissions
        judge_prompt = f"""
        You are an expert art critic judging AI-generated images for a daily challenge. Today's challenge is:
        "{submission.challenge.description}"

        Compare these two submissions:

        Submission 1:
        Prompt: {user_submission.prompt}
        Image: [Generated based on this prompt]

        Submission 2:
        Prompt: {submission.prompt}
        Image: [Generated based on this prompt]

        Evaluate each submission based on:
        1. How well the prompt aligns with the challenge requirements
        2. How effectively the generated image fulfills the prompt's intent
        3. Overall creativity and originality
        4. Technical execution and quality

        Provide a detailed analysis explaining which submission better meets the challenge criteria and why.
        Be specific about the strengths and weaknesses of each submission in relation to the challenge.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert art critic specializing in evaluating AI-generated images against specific challenge criteria."},
                    {"role": "user", "content": judge_prompt}
                ]
            )
            
            judge_feedback = response.choices[0].message.content
            
            # Create challenge result
            result = ChallengeResult.objects.create(
                challenge=submission.challenge,
                winner=user_submission,
                loser=submission,
                judge_feedback=judge_feedback
            )
            
            # Update user profiles
            winner_profile, _ = UserProfile.objects.get_or_create(user=user_submission.user)
            loser_profile, _ = UserProfile.objects.get_or_create(user=submission.user)
            
            winner_profile.points += 10
            winner_profile.wins += 1
            loser_profile.losses += 1
            
            winner_profile.save()
            loser_profile.save()
            
            messages.success(request, 'Challenge completed!')
            return redirect('challenge_result', result_id=result.id)
            
        except Exception as e:
            messages.error(request, f'Error judging submissions: {str(e)}')
            return redirect('challenge_user', submission_id=submission_id)
    
    return render(request, 'challenges/challenge.html', {
        'submission': submission,
        'user_submission': user_submission
    })

def leaderboard(request):
    profiles = UserProfile.objects.all().order_by('-points')
    return render(request, 'challenges/leaderboard.html', {'profiles': profiles})

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    submissions = UserSubmission.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'challenges/profile.html', {
        'profile': profile,
        'submissions': submissions,
        'form': form
    })

@login_required
def delete_submission(request, submission_id):
    submission = get_object_or_404(UserSubmission, id=submission_id)
    
    # Check if the user owns this submission
    if submission.user != request.user:
        messages.error(request, 'You can only delete your own submissions.')
        return redirect('home')
    
    if request.method == 'POST':
        # Delete the image file from storage
        if submission.generated_image:
            default_storage.delete(submission.generated_image.path)
        
        # Delete the submission
        submission.delete()
        messages.success(request, 'Your submission has been deleted.')
        return redirect('home')
    
    return render(request, 'challenges/delete_submission.html', {'submission': submission})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def challenge_result(request, result_id):
    result = get_object_or_404(ChallengeResult, id=result_id)
    return render(request, 'challenges/challenge_result.html', {'result': result})

def view_challenge(request, challenge_id):
    challenge = get_object_or_404(DailyChallenge, id=challenge_id)
    submissions = UserSubmission.objects.filter(challenge=challenge).select_related('user', 'user__userprofile').order_by('-created_at')
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
    }
    return render(request, 'challenges/view_challenge.html', context)

def gallery(request):
    # Get all submissions ordered by date
    submissions = UserSubmission.objects.all().order_by('-created_at')
    return render(request, 'challenges/gallery.html', {'submissions': submissions})
