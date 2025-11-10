from django.urls import path
from . import views

urlpatterns = [
    path('progress/<int:habit_id>/checkin/', views.ProgressCheckinView.as_view(), name='progress-checkin'),
    
]
