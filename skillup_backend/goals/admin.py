from django.contrib import admin
from .models import Goal,Habit,ProgressLog,Badge,UserBadge
# Register your models here.
admin.site.register(Goal)
admin.site.register(Habit)
admin.site.register(ProgressLog)
admin.site.register(Badge)
admin.site.register(UserBadge)