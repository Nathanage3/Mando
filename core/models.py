from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from .managers import CustomUserManager
from django.utils.timezone import now
from datetime import timedelta
import uuid


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True,
                                        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png', 'jpeg'])])
    website = models.URLField(blank=True, null=True)
    username = None  # Remove the default username field

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Remove username from required fields

    objects = CustomUserManager()
    
    def __str__(self):
        return f'Hello, {self.first_name } {self.last_name}'


class UserActivationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activation_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} - {self.token}'
    
    def is_expired(self):
        expiration_time = self.created_at + timedelta(hours=24)
        return now() > expiration_time
