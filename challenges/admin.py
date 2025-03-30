from django.contrib import admin
from .models import DailyChallenge, UserSubmission, ChallengeResult, UserProfile

@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'category', 'is_active', 'submission_count')
    list_filter = ('is_active', 'category', 'date')
    search_fields = ('title', 'description')
    ordering = ('-date',)
    actions = ['activate_challenges', 'deactivate_challenges']
    
    def submission_count(self, obj):
        return obj.usersubmission_set.count()
    submission_count.short_description = 'Submissions'
    
    def activate_challenges(self, request, queryset):
        queryset.update(is_active=True)
    activate_challenges.short_description = "Activate selected challenges"
    
    def deactivate_challenges(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_challenges.short_description = "Deactivate selected challenges"

admin.site.register(UserSubmission)
admin.site.register(ChallengeResult)
admin.site.register(UserProfile)
