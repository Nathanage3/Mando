from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer,\
                               UserSerializer as BaseUserSerializer, \
                               SetPasswordSerializer as BaseSetPasswordSerializer
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User


class UserCreateSerializer(BaseUserCreateSerializer):
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    class Meta(BaseUserCreateSerializer.Meta):
        model = User  # Ensure this points to your custom User model
        fields = ['email', 'password', 'first_name', 'last_name', 'role']


class UserSerializer(BaseUserSerializer):
    profile_picture = serializers.ImageField(read_only=True)
   
    #role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    class Meta(BaseUserSerializer.Meta):
        model = User  # Ensure this points to your custom User model
        fields = ['email', 'first_name', 'last_name', 'role', 'profile_picture']


class SetPasswordSerializer(BaseSetPasswordSerializer):
    new_password = serializers.CharField(write_only=True)
    re_new_password = serializers.CharField(write_only=True)

    class Meta:
        model = User  # Ensure this points to your custom User model
        fields = ['current_password', 'new_password', 're_new_password']


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    re_new_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['current_password', 'new_password', 're_new_password']

    def validate(self, attrs):
        if attrs['new_password'] != attrs['re_new_password']:
            raise serializers.ValidationError({"new_password": "The two password fields didn't match."})
        validate_password(attrs['new_password'])
        return attrs

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("The current password is incorrect.")
        return value