from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Goal, Habit, ProgressLog,Badge,UserBadge
User=get_user_model()
class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

class HabitSerializer(serializers.ModelSerializer):
     class Meta:
        model = Habit
        fields = ('id', 'name', 'frequency', 'goal','current_streak','target_value')
        read_only_fields = ('goal',)
     
    
class ProgressLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressLog
        fields = '__all__'
        read_only_fields = ('date',)


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ('id','name','description','xp_required','icon')

class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    class Meta:
        model = UserBadge
        fields = ('id','badge','earned_on')


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'xp_points', 'level', 'avatar')