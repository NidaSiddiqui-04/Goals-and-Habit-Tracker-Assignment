from django.contrib import admin
from .models import Goal,Habit,ProgressLog,Badge,UserBadge
# Register your models here.
admin.site.register(Goal)
admin.site.register(Habit)
admin.site.register(ProgressLog)

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'xp_required','days_required')
    search_fields = ('name',)
    list_filter = ('xp_required',)

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_on')
    search_fields = ('user__username','badge__name')
    raw_id_fields = ('user', 'badge')