from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('challenges/', views.challenge_list, name='challenge_list'),
    path('challenges/create/', views.create_challenge, name='create_challenge'),
    path('challenges/generate-random/', views.generate_random_challenge, name='generate_random_challenge'),
    path('challenges/detail/<int:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    path('challenges/submit/<int:challenge_id>/', views.submit_challenge, name='submit_challenge'),
    path('challenges/judge/<int:challenge_id>/', views.judge_challenge, name='judge_challenge'),
    path('challenges/challenge/<int:submission_id>/', views.challenge_user, name='challenge_user'),
    path('challenges/result/<int:result_id>/', views.challenge_result, name='challenge_result'),
    path('gallery/', views.gallery, name='gallery'),
    path('profile/', views.profile, name='my_profile'),
    path('profile/<str:username>/', views.profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('delete/<int:submission_id>/', views.delete_submission, name='delete_submission'),
    path('submission/<int:submission_id>/like/', views.like_submission, name='like_submission'),
    path('submission/<int:submission_id>/comment/', views.add_comment, name='add_comment'),
    path('submission/<int:submission_id>/comments/', views.get_comments, name='get_comments'),
    path('about/', views.about, name='about'),
] 