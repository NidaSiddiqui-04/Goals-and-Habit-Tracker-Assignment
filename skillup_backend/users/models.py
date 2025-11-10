from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    xp_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak_count = models.IntegerField(default=0)
    avatar = models.ImageField(default="avatar.jpg",upload_to="avatar")
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.username
