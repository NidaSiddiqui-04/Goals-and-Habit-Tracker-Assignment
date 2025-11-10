from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Goal, Habit,ProgressLog
from .serializers import GoalSerializer, HabitSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from rest_framework.generics import CreateAPIView


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Habit.objects.filter(goal__user=self.request.user)

    def perform_create(self, serializer):
        goal = serializer.validated_data.get('goal')
        if goal.user != self.request.user:
            raise PermissionDenied("Cannot add habit to a goal you don't own.")
        serializer.save()


class ProgressCheckinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, habit_id):
        habit = Habit.objects.filter(id=habit_id, goal__user=request.user).first()
        if not habit:
            raise PermissionDenied("Not your habit.")

        today = timezone.localdate()
        log, created = ProgressLog.objects.get_or_create(habit=habit, date=today)

        if log.completed:
            return Response({"detail": "Already checked in today."}, status=400)

        log.completed = True
        log.save()

        
        prev = ProgressLog.objects.filter(habit=habit, completed=True, date__lt=today).order_by('-date').first()
        if prev and (today - prev.date).days == 1:
            habit.current_streak += 1
        else:
            habit.current_streak = 1
        habit.save()

        
        user = request.user
        user.xp_points += 10
        user.save()

        return Response({
            "message": "Check-in recorded!",
            "current_streak": habit.current_streak,
            "xp_total": user.xp_points,
        }, status=201)
    

def goals_list(request):

    return render(request, 'goals/goal_list.html',)

def goal_create(request):
    return render(request, 'goals/goals_create.html')

def goal_update(request, id):
    
    return render(request, 'goals/goals_update.html', {'goal_id':id})

def goal_delete(request, id):
    return render(request, 'goals/goals_delete.html', {'goal_id': id})
