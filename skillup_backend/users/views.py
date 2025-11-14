from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from goals.models import Goal
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserSerializer
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets

User = get_user_model()

class RegisterPageView(TemplateView):
    template_name = "register.html"
    parser_classes = (MultiPartParser, FormParser)

class LoginPageView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True
    # where to redirect after successful login
    next_page = reverse_lazy('dashboard')   # or your dashboard URL name

    def form_valid(self, form):
        """If the form is valid, log the user in and redirect."""
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, "Account not active.")
            return redirect('login')
        login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        """Return the URL to redirect to after successful login."""
        return self.next_page
    


class dashboard(TemplateView):
   
    
    template_name='dashboard.html'
    
     
    
class Logout(TemplateView):
    template_name='logout.html'
    
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    parser_classes = (MultiPartParser, FormParser)

    permission_classes = [AllowAny]
    
    


class MeView(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


def user_profile(request):
    return render(request,"user_profile.html")

def edit_profile(request):
    return render(request,'edit_profile.html')