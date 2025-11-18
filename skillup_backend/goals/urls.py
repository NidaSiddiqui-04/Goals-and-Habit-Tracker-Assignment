from django.urls import path
from . import views

urlpatterns = [
    path('progress/<int:habit_id>/checkin/', views.ProgressCheckinView.as_view(), name='progress-checkin'),
    path('analytics/overview/',views.DashboardView.as_view(),name="dashboard_analytic"),
    path('weekly/report/',views.CurrentWeekCompleteReportView.as_view(),name="weekly_report"),
    path('user_badges/',views.MyBadgesListView.as_view(),name="user_badges"),
    path('leaderboard/',views.LeaderboardView.as_view(),name='leader_board')
]
