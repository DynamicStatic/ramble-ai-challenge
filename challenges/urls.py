from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('submit/', views.submit_challenge, name='submit_challenge'),
    path('challenge/<int:submission_id>/', views.challenge_user, name='challenge_user'),
    path('challenge/result/<int:result_id>/', views.challenge_result, name='challenge_result'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('profile/', views.profile, name='profile'),
    path('delete/<int:submission_id>/', views.delete_submission, name='delete_submission'),
    path('challenge_result/<int:result_id>/', views.challenge_result, name='challenge_result'),
    path('view_challenge/<int:challenge_id>/', views.view_challenge, name='view_challenge'),
    path('gallery/', views.gallery, name='gallery'),
] 