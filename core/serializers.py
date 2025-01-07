from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer,\
                               UserSerializer as BaseUserSerializer, \
                               SetPasswordSerializer as BaseSetPasswordSerializer
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User

from rest_framework import serializers
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import User
import logging

logger = logging.getLogger(__name__)

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']

    def create(self, validated_data):
        # Create the user
        user = User.objects.create_user(**validated_data)
        user.is_active = False  # Ensure the user is inactive initially
        user.save()
        
        return user


class UserSerializer(BaseUserSerializer):
    profile_picture = serializers.ImageField(read_only=True)
   
    #role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    class Meta(BaseUserSerializer.Meta):
        model = User  # Ensure this points to your custom User model
        fields = ['email', 'first_name', 'last_name', 'bio', 'website', 'profile_picture']
