from django.db import models

from django.db import models
from django.conf import settings

class Goal(models.Model):
    CATEGORY_CHOICES = [
        ('fitness','Fitness'),
        ('coding','Coding'),
        ('reading','Reading'),
        ('custom','Custom'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='custom')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Habit(models.Model):
    FREQUENCY_CHOICES = [('daily','Daily'), ('weekly','Weekly')]
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=255)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    target_value = models.IntegerField(default=1)
    current_streak = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.goal.title})"

 
class ProgressLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('habit', 'date')

    def __str__(self):
        return f"{self.habit.name} - {self.date}"



class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    xp_required = models.IntegerField(null=True,blank=True)
    days_required=models.IntegerField(null=True,blank=True)
    icon = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_on']

    def __str__(self):
        return f"{self.user.username} — {self.badge.name}"