"""
URL configuration for skillup_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter,SimpleRouter
from goals.views import GoalViewSet, HabitViewSet 
from users.views import RegisterView, MeView,RegisterPageView,LoginPageView,dashboard,Logout,user_profile,edit_profile
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from goals import urls
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_nested.routers import NestedSimpleRouter
from goals.views import goal_delete,goal_update,goals_list,goal_create,habit_list,habit_create,habit_delete,habit_completion,leaderboard

router =SimpleRouter()
router.register(r'goals', GoalViewSet, basename='goals')
goals_router = NestedSimpleRouter(router, r'goals', lookup='goal')
goals_router.register(r'habits', HabitViewSet, basename='goal-habits')
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path("api/",include('goals.urls')),
     path('api/', include(goals_router.urls)),

    
    path('api/auth/register/', RegisterView.as_view(), name='auth-register'),
    path('register/', RegisterPageView.as_view(), name='register-page'),
    path('login/',LoginPageView.as_view(),name='login'),
    path('logout/',Logout.as_view(),name="logout"),
    path('dashboard/',dashboard.as_view(),name='dashboard'),
    path( 'api/auth/me/',  MeView.as_view({'get': 'retrieve', 'put': 'update'}), name='auth-me'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user_profile/',user_profile,name="user_profile"),
    path('profile/edit/',edit_profile,name="edit_profile"),
    path('goal_list/',goals_list, name='goal_list'),
    path('goals/create/', goal_create, name='goal_create'), 
    path('goals/<int:id>/update/', goal_update, name='goal_update'),
    path('goals/<int:id>/delete/', goal_delete, name='goal_delete'),
    path('leaderboard/',leaderboard,name="leaderboard"),
    path('<int:id>/habit',habit_list,name='habit_list'),
    path('<int:id>/habit/create/',habit_create,name="habit_create"),
    path('<int:id>/habit/delete/<int:pk>/',habit_delete,name="habit_delete"),
    path('progresslog/',habit_completion,name="habit_completion"),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
 ]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
