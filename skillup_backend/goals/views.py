from django.shortcuts import render
from rest_framework import viewsets,status
from rest_framework.permissions import IsAuthenticated,AllowAny
from .models import Goal, Habit,ProgressLog,Badge,UserBadge
from .serializers import GoalSerializer, HabitSerializer,ProgressLogSerializer,UserBadgeSerializer,BadgeSerializer,LeaderboardSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework.generics import ListAPIView
import logging, re
logger = logging.getLogger(__name__)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction, IntegrityError

from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView

User=get_user_model()
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
        goal_pk = self.kwargs.get('goal_pk')
        # Validate that the goal exists and belongs to the user
        try:
            goal = Goal.objects.get(pk=goal_pk, user=self.request.user)
        except Goal.DoesNotExist:
            raise PermissionDenied("Goal does not exist or you don't own it.")
        return Habit.objects.filter(goal=goal)

    def perform_create(self, serializer):
        goal_pk = self.kwargs.get('goal_pk')
        try:
            goal = Goal.objects.get(pk=goal_pk, user=self.request.user)
        except Goal.DoesNotExist:
            raise PermissionDenied("Goal does not exist or you don't own it.")
        serializer.save(goal=goal)



class ProgressCheckinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, habit_id):
        habit = Habit.objects.filter(id=habit_id, goal__user=request.user).first()
        if not habit:
            raise PermissionDenied("Not your habit.")
        

        today=timezone.localdate()
        log, created = ProgressLog.objects.get_or_create(habit=habit, date=today)

        if log.completed:
            return Response({"detail": "Already checked in today."}, status=400)

        log.completed = True
        log.save()

        
        prev = ProgressLog.objects.filter(habit=habit, completed=True, date__lt=today).order_by('-date').first()
        user=request.user
        if prev and (today - prev.date).days == 1:
            user.streak_count += 1
            habit.current_streak+=1
        else:
            user.streak_count = 1
            habit.current_streak =1

        habit.save()
        user.save()

        
        
        
        XP_PER_CHECKIN = 10
        user.xp_points = (user.xp_points or 0) + XP_PER_CHECKIN
        user.save()
        newly_awarded = []

        # 5a) XP-based badges: Badge.xp_required <= user.xp_points
        try:
            xp_badges = Badge.objects.filter(xp_required__lte=user.xp_points).order_by('xp_required', 'id')
            for b in xp_badges:
                try:
                    ub, created = UserBadge.objects.get_or_create(user=user, badge=b)
                    if created:
                        newly_awarded.append(ub)
                        logger.info("XP badge awarded: %s to %s", b.name, user.username)
                except IntegrityError:
                    continue
        except Exception as e:
            logger.exception("Error awarding XP badges: %s", e)

        # 2) Streak-based badges (STRICT) - do NOT include xp_required==0 candidates
     
        try:
            # Exclude streak-named badges here so they are NOT awarded by the XP rule
            xp_badges = Badge.objects.filter(xp_required__lte=user.xp_points).exclude(name__icontains='streak').order_by('xp_required', 'id')
            for b in xp_badges:
                try:
                    ub, created = UserBadge.objects.get_or_create(user=user, badge=b)
                    if created:
                        newly_awarded.append(ub)
                except IntegrityError:
                    # already created concurrently; skip
                    continue
                except Exception:
                    # log if needed, but continue awarding other badges
                    continue
        except Exception:
            # defensive: don't break check-in if badge query fails
            pass

        
        resp = {
            'log': ProgressLogSerializer(log).data,
            'habit': {
                'id': habit.id,
                'name': habit.name,
                'current_streak': habit.current_streak
            },
            'xp_awarded': XP_PER_CHECKIN,
            'total_xp': user.xp_points,
            'awarded_badges': UserBadgeSerializer(newly_awarded, many=True).data if newly_awarded else []
        }
        return Response(resp, status=status.HTTP_201_CREATED)
        


class BadgeListView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Badge.objects.all().order_by('xp_required', 'name')
    serializer_class = BadgeSerializer


class MyBadgesListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserBadgeSerializer

    def get_queryset(self):
        return UserBadge.objects.filter(user=self.request.user).order_by('-earned_on')[:1]



class LeaderboardView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = LeaderboardSerializer

    def get_queryset(self):
        return User.objects.order_by('-xp_points')[:50]

def check_and_award_badges(user):
    """
    This function checks user's XP and awards badges if thresholds are met.
    """
    badges = Badge.objects.filter(xp_required__lte=user.xp_points)  # all badges user qualifies for

    for badge in badges:
        already_earned = UserBadge.objects.filter(user=user, badge=badge).exists()
        if not already_earned:
            UserBadge.objects.create(user=user, badge=badge)


def goals_list(request):

    return render(request, 'goals/goal_list.html')

def habit_completion(request):
    habit=Habit.objects.filter(id=habit.id,goal__user=request.user).first()
    today=timezone.localdate()
    log, created = ProgressLog.objects.get_or_create(habit=habit, date=today)

    return render(request,'goals/goals_list.html',{'log':log})

def goal_create(request):
    return render(request, 'goals/goals_create.html')

def goal_update(request, id):
    
    return render(request, 'goals/goals_update.html', {'goal_id':id})

def goal_delete(request, id):
    return render(request, 'goals/goals_delete.html', {'goal_id': id})


def habit_list(request,id):
    return render(request,'goals/habit_list.html',{'goal_id':id})

def habit_create(request,id):
    return render(request,'goals/habit_create.html',{'goal_id':id})

def habit_delete(request,id,pk):
    return render(request,'goals/habit_delete.html',{'goal_id':id,'habit_id':pk})