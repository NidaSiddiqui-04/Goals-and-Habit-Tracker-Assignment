from django.shortcuts import render
from rest_framework import viewsets,status
from rest_framework.permissions import IsAuthenticated,AllowAny
from .models import Goal, Habit,ProgressLog,Badge,UserBadge
from .serializers import GoalSerializer, HabitSerializer,ProgressLogSerializer,UserBadgeSerializer,BadgeSerializer,LeaderboardSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework.generics import ListAPIView,RetrieveAPIView
import logging, re
logger = logging.getLogger(__name__)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction, IntegrityError
import datetime
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

        if user.xp_points>=100:
            user.level=2
        if user.xp_points>=200:
            user.level=3
        if user.xp_points>=300:
            user.level=4
        if user.xp_points>=400:
            user.level=5    
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
            'level':user.level,
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
        return User.objects.order_by('-xp_points')[:3]
 
class DashboardView(RetrieveAPIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        goals=Goal.objects.filter(user=self.request.user)
        user=request.user
        resp ={
            'no_of_goals':goals.count(),
             'total_xp_point':user.xp_points,
             'streaks':user.streak_count,
              'level':user.level
        }
        return Response(resp,status=status.HTTP_200_OK)


class CurrentWeekCompleteReportView(RetrieveAPIView):
    """
    GET /api/weekly/report/
    Returns a complete weekly report for the authenticated user for the current week (Monday - Sunday).
    """
    permission_classes = [IsAuthenticated]

    def _current_week_range(self):
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + datetime.timedelta(days=6)          # Sunday
        return start_of_week, end_of_week

    def _count_logs_for_habit(self, habit, start_of_week, end_of_week):
          return ProgressLog.objects.filter(habit=habit, date__range=[start_of_week, end_of_week]).count()
           
        

    def get(self, request):
        start_of_week, end_of_week = self._current_week_range()
    
        goals = Goal.objects.filter(user=request.user)

        overall_habit_count = 0
        overall_total_target = 0
        overall_total_count = 0
        per_goal_reports = []

        for goal in goals:
            habits = Habit.objects.filter(goal=goal)
            goal_habits_report = []
            goal_total_target = 0.0
            goal_total_count = 0.0

            for habit in habits:
                count = self._count_logs_for_habit(habit, start_of_week,end_of_week)

                if habit.frequency == 'daily':
                    weekly_target = habit.target_value * 7
                else:
                    weekly_target = habit.target_value

                percentage = (count / weekly_target * 100) if weekly_target > 0 else 0.0

                habit_data = {
                    'id': habit.id,
                    'name': habit.name,
                    'target': weekly_target,
                    'frequency': habit.frequency,
                    'percentage': round(percentage, 2),
                    'streaks':habit.current_streak,
                }

                goal_habits_report.append(habit_data)

                overall_habit_count += 1
                goal_total_target += weekly_target
                goal_total_count += count
                overall_total_target += weekly_target
                overall_total_count += count
                
            per_goal_reports.append({
                'goal_id': goal.id,
                'goal_name':goal.title,
                'habits': goal_habits_report,
                'goal_total_target': goal_total_target,
                'goal_total_count': goal_total_count,
                'goal_percentage': round((goal_total_count / goal_total_target * 100), 2) if goal_total_target > 0 else 0.0
            })

        overall_percentage = round((overall_total_count / overall_total_target * 100), 2) if overall_total_target > 0 else 0.0

        resp = {
            'week_start': start_of_week.isoformat(),
            'week_end': end_of_week.isoformat(),
            'overall': {
                'total_goals': goals.count(),
                'total_habits': overall_habit_count,
                'total_target': overall_total_target,
                'total_count': overall_total_count,
                'overall_percentage': overall_percentage,
            },
            'goals': per_goal_reports
        }

        return Response(resp, status=status.HTTP_200_OK)



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


def leaderboard(request):
    return render(request,'goals/leaderboard.html')

def weeklyreport(request):
    return render(request,'goals/weekly_report.html')