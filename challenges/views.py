from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from .models import DailyChallenge, UserSubmission, ChallengeResult, UserProfile, Challenge, Like, Comment
import os
from django.conf import settings
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .forms import UserProfileForm, ChallengeForm
from django.db.models import Count
import base64
from io import BytesIO
from PIL import Image
import json
from django.contrib.auth.models import User
from django.http import JsonResponse

# Initialize BLIP model and processor only when needed
processor = None
model = None

def get_blip_model():
    global processor, model
    if processor is None or model is None:
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        except Exception as e:
            print(f"Error initializing BLIP model: {str(e)}")
            return None, None
    return processor, model

def generate_image_caption(image_path):
    """Generate a caption for an image using BLIP."""
    try:
        processor, model = get_blip_model()
        if processor is None or model is None:
            return "Error: Could not initialize image captioning model"
            
        # Load and preprocess the image
        image = Image.open(image_path).convert('RGB')
        inputs = processor(image, return_tensors="pt")
        
        # Generate caption
        outputs = model.generate(**inputs, max_length=100)
        caption = processor.decode(outputs[0], skip_special_tokens=True)
        
        return caption
    except Exception as e:
        print(f"Error generating caption: {str(e)}")
        return "Error generating image caption"

# Add debug logging
print(f"OpenAI API Key loaded: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
print(f"API Key length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")

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
    # Get active challenges
    active_challenges = Challenge.objects.filter(
        is_active=True,
        end_date__gt=timezone.now()
    ).order_by('-created_at')
    
    # Get daily challenge
    daily_challenge = active_challenges.filter(type='daily').first()
    
    # Get random challenges
    random_challenges = active_challenges.filter(type='random')
    
    # Get recent submissions
    submissions = UserSubmission.objects.select_related('user', 'challenge').order_by('-created_at')[:10]
    
    # Get completed challenges
    completed_challenges = Challenge.objects.filter(
        end_date__lt=timezone.now()
    ).order_by('-end_date')[:10]
    
    context = {
        'daily_challenge': daily_challenge,
        'random_challenges': random_challenges,
        'submissions': submissions,
        'completed_challenges': completed_challenges,
    }
    return render(request, 'challenges/home.html', context)

@login_required
def submit_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    if not challenge.is_active or challenge.end_date < timezone.now():
        messages.error(request, 'This challenge is no longer active.')
        return redirect('challenge_list')
    
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        if not prompt:
            messages.error(request, 'Please provide a prompt')
            return redirect('submit_challenge', challenge_id=challenge_id)
        
        try:
            print(f"Starting image generation for prompt: {prompt}")
            # Get the next submission number for this user and challenge
            last_submission = UserSubmission.objects.filter(
                user=request.user,
                challenge=challenge
            ).order_by('-submission_number').first()
            
            next_submission_number = (last_submission.submission_number + 1) if last_submission else 1
            print(f"Next submission number: {next_submission_number}")
            
            # Generate image using OpenAI API
            print("Making request to OpenAI API...")
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "size": "1024x1024",
                "quality": "standard",
                "n": 1
            }
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            print("Received response from OpenAI API")
            
            # Get the image URL
            image_url = response.json()['data'][0]['url']
            print(f"Image URL received: {image_url}")
            
            # Download the image
            print("Downloading image...")
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            print("Image downloaded successfully")
            
            # Generate a filename
            filename = f"submissions/{request.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
            print(f"Saving image as: {filename}")
            
            # Save the image to media storage
            image_path = default_storage.save(filename, ContentFile(img_response.content))
            print(f"Image saved successfully at: {image_path}")
            
            # Create submission with the local image path
            submission = UserSubmission.objects.create(
                user=request.user,
                challenge=challenge,
                prompt=prompt,
                generated_image=image_path,
                submission_number=next_submission_number
            )
            print(f"Submission created successfully with ID: {submission.id}")
            
            messages.success(request, 'Your submission has been created!')
            return render(request, 'challenges/submit_result.html', {
                'submission': submission,
                'challenge': challenge
            })
            
        except Exception as e:
            print(f"Error in submit_challenge: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            messages.error(request, f'Error generating image: {str(e)}')
            return redirect('submit_challenge', challenge_id=challenge_id)
    
    return render(request, 'challenges/submit.html', {'challenge': challenge})

@login_required
def challenge_user(request, submission_id):
    submission = get_object_or_404(UserSubmission, id=submission_id)
    
    # Get all submissions by the current user for this challenge
    user_submissions = UserSubmission.objects.filter(
        user=request.user,
        challenge=submission.challenge
    ).order_by('-created_at')
    
    if not user_submissions.exists():
        messages.error(request, 'You need to submit an image first')
        return redirect('submit_challenge', challenge_id=submission.challenge.id)
    
    if request.method == 'POST':
        # Get the selected user submission
        user_submission_id = request.POST.get('user_submission')
        if not user_submission_id:
            messages.error(request, 'Please select your submission')
            return redirect('challenge_user', submission_id=submission_id)
            
        user_submission = get_object_or_404(UserSubmission, id=user_submission_id, user=request.user)
        
        # Use AI to judge the submissions
        judge_prompt = f"""
        You are an art critic judging two AI-generated images for a challenge. The challenge is: "{submission.challenge.description}"

        Compare these two submissions and decide which one better meets the challenge criteria.
        You MUST choose a winner - there cannot be a tie or no winner.
        Keep your response brief and to the point - just 2-3 sentences explaining which submission wins and why.
        Your response MUST end with either "Submission 1 wins" or "Submission 2 wins" on a new line.

        Submission 1 (Your Submission):
        Prompt: {user_submission.prompt}
        Image: {user_submission.generated_image.url}

        Submission 2 (Opponent's Submission):
        Prompt: {submission.prompt}
        Image: {submission.generated_image.url}
        """
        
        try:
            # Make API call to OpenAI for judging
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4-turbo",
                "messages": [
                    {
                        "role": "user",
                        "content": judge_prompt
                    }
                ],
                "max_tokens": 200  # Reduced token limit for shorter response
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            judge_feedback = response.json()['choices'][0]['message']['content']
            
            # Parse the judge's feedback to determine winner
            feedback_lines = judge_feedback.lower().split('\n')
            winner_line = None
            
            # Look for the winner declaration in the last few lines
            for line in feedback_lines[-3:]:
                if "submission 1 wins" in line:
                    winner_submission = user_submission
                    loser_submission = submission
                    winner_line = line
                    break
                elif "submission 2 wins" in line:
                    winner_submission = submission
                    loser_submission = user_submission
                    winner_line = line
                    break
            
            # If no winner line found, try to find it anywhere in the feedback
            if not winner_line:
                if "submission 1 wins" in judge_feedback.lower():
                    winner_submission = user_submission
                    loser_submission = submission
                elif "submission 2 wins" in judge_feedback.lower():
                    winner_submission = submission
                    loser_submission = user_submission
                else:
                    # If still no winner found, make a decision based on the feedback
                    if "submission 1" in judge_feedback.lower() and "submission 2" in judge_feedback.lower():
                        # If both submissions are mentioned, choose the one mentioned first
                        if judge_feedback.lower().find("submission 1") < judge_feedback.lower().find("submission 2"):
                            winner_submission = user_submission
                            loser_submission = submission
                        else:
                            winner_submission = submission
                            loser_submission = user_submission
                    else:
                        # If only one submission is mentioned, it's the winner
                        if "submission 1" in judge_feedback.lower():
                            winner_submission = user_submission
                            loser_submission = submission
                        else:
                            winner_submission = submission
                            loser_submission = user_submission

            # Create challenge result
            challenge_result = ChallengeResult.objects.create(
                challenge=submission.challenge,
                winner=winner_submission,
                loser=loser_submission,
                judge_feedback=judge_feedback
            )
            
            # Update user profiles
            winner_profile, _ = UserProfile.objects.get_or_create(user=winner_submission.user)
            loser_profile, _ = UserProfile.objects.get_or_create(user=loser_submission.user)
            
            winner_profile.points += 10
            winner_profile.wins += 1
            loser_profile.losses += 1
            
            winner_profile.save()
            loser_profile.save()
            
            messages.success(request, 'Challenge completed!')
            return redirect('challenge_result', result_id=challenge_result.id)
            
        except Exception as e:
            messages.error(request, f'Error judging submissions: {str(e)}')
            return redirect('challenge_user', submission_id=submission_id)
    
    context = {
        'submission': submission,
        'user_submissions': user_submissions,
        'challenge': submission.challenge
    }
    return render(request, 'challenges/challenge.html', context)

def leaderboard(request):
    # Get all profiles ordered by points, then wins, then losses
    profiles = UserProfile.objects.select_related('user').order_by('-points', '-wins', 'losses')
    return render(request, 'challenges/leaderboard.html', {'profiles': profiles})

@login_required
def profile(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
        profile = get_object_or_404(UserProfile, user=user)
    else:
        profile = get_object_or_404(UserProfile, user=request.user)
    
    submissions = UserSubmission.objects.filter(user=profile.user).order_by('-created_at')
    
    # Handle profile editing
    if request.method == 'POST' and request.user == profile.user:
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('my_profile')
    else:
        form = UserProfileForm(instance=profile) if request.user == profile.user else None
    
    context = {
        'profile': profile,
        'submissions': submissions,
        'is_own_profile': request.user == profile.user,
        'form': form
    }
    return render(request, 'challenges/profile.html', context)

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
    try:
        result = get_object_or_404(ChallengeResult, id=result_id)
        # Ensure the images exist
        if not result.winner.generated_image or not result.loser.generated_image:
            messages.error(request, 'Error: One or more images are missing.')
            return redirect('home')
        return render(request, 'challenges/challenge_result.html', {'result': result})
    except Exception as e:
        messages.error(request, f'Error displaying challenge result: {str(e)}')
        return redirect('home')

def view_challenge(request, challenge_id):
    challenge = get_object_or_404(DailyChallenge, id=challenge_id)
    submissions = UserSubmission.objects.filter(challenge=challenge).select_related('user', 'user__userprofile').order_by('-created_at')
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
    }
    return render(request, 'challenges/view_challenge.html', context)

@login_required
def gallery(request):
    submissions = UserSubmission.objects.select_related('user', 'challenge').prefetch_related('likes').order_by('-created_at')
    return render(request, 'challenges/gallery.html', {'submissions': submissions})

@login_required
def challenge_list(request):
    # Get active challenges
    active_challenges = Challenge.objects.filter(
        is_active=True,
        end_date__gt=timezone.now()
    ).order_by('-created_at')
    
    # Get daily challenge
    daily_challenge = active_challenges.filter(type='daily').first()
    
    # Get random challenges
    random_challenges = active_challenges.filter(type='random')
    
    # If no random challenges exist, generate one
    if not random_challenges.exists():
        Challenge.generate_random_challenge()
        random_challenges = active_challenges.filter(type='random')
    
    context = {
        'daily_challenge': daily_challenge,
        'random_challenges': random_challenges,
    }
    return render(request, 'challenges/challenge_list.html', context)

@login_required
def create_challenge(request):
    if not request.user.is_staff:
        return redirect('challenge_list')
        
    if request.method == 'POST':
        form = ChallengeForm(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.type = 'daily'  # Admin-created challenges are always daily
            challenge.save()
            return redirect('challenge_list')
    else:
        form = ChallengeForm()
    
    return render(request, 'challenges/create_challenge.html', {'form': form})

@login_required
def generate_random_challenge(request):
    if not request.user.is_staff:
        return redirect('challenge_list')
        
    challenge = Challenge.generate_random_challenge()
    if challenge:
        messages.success(request, 'Random challenge generated successfully!')
    else:
        messages.error(request, 'Failed to generate random challenge.')
    
    return redirect('challenge_list')

@login_required
def edit_profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'challenges/edit_profile.html', {'form': form})

@login_required
def challenge_detail(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    submissions = UserSubmission.objects.filter(challenge=challenge).order_by('-created_at')
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
    }
    return render(request, 'challenges/challenge_detail.html', context)

@login_required
def judge_challenge(request, challenge_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to judge challenges.")
        return redirect('challenge_list')
    
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    submissions = UserSubmission.objects.filter(challenge=challenge).order_by('-created_at')
    
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')
        
        if submission_id and score:
            submission = get_object_or_404(UserSubmission, pk=submission_id)
            submission.score = int(score)
            submission.feedback = feedback
            submission.save()
            messages.success(request, 'Submission judged successfully!')
            return redirect('challenge_detail', challenge_id=challenge_id)
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
    }
    return render(request, 'challenges/judge_challenge.html', context)

@login_required
def like_submission(request, submission_id):
    print(f"Like submission called for submission {submission_id}")
    submission = get_object_or_404(UserSubmission, id=submission_id)
    like, created = Like.objects.get_or_create(user=request.user, submission=submission)
    
    if not created:
        like.delete()
        print(f"Unliked submission {submission_id}")
        return JsonResponse({'status': 'unliked', 'likes_count': submission.likes.count()})
    
    print(f"Liked submission {submission_id}")
    return JsonResponse({'status': 'liked', 'likes_count': submission.likes.count()})

@login_required
def add_comment(request, submission_id):
    if request.method == 'POST':
        submission = get_object_or_404(UserSubmission, id=submission_id)
        text = request.POST.get('text')
        
        if text:
            comment = Comment.objects.create(
                user=request.user,
                submission=submission,
                text=text
            )
            
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'text': comment.text,
                    'user': comment.user.username,
                    'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
                }
            })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_comments(request, submission_id):
    submission = get_object_or_404(UserSubmission, id=submission_id)
    comments = submission.comments.all()
    
    comments_data = [{
        'user': comment.user.username,
        'text': comment.text,
        'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
    } for comment in comments]
    
    return JsonResponse({'comments': comments_data})
