from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer,\
                               UserSerializer as BaseUserSerializer, \
                               SetPasswordSerializer as BaseSetPasswordSerializer
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User


# class UserCreateSerializer(BaseUserCreateSerializer):
#     role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
#     class Meta(BaseUserCreateSerializer.Meta):
#         model = User  # Ensure this points to your custom User model
#         fields = ['email', 'password', 'first_name', 'bio', 'website', 'last_name', 'role']

# File location: core/serializers.py

# from rest_framework import serializers
# from core.models import User, UserActivationToken
# from django.core.mail import send_mail
# from django.conf import settings
# from django.template.loader import render_to_string
# import uuid
# import logging

# logger = logging.getLogger(__name__)

# class UserCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['email', 'password']

#     def create(self, validated_data):
#         user = User.objects.create_user(**validated_data)
#         user.is_active = False
#         user.save()

#         # Generate and store the token
#         token = uuid.uuid4()
#         print("Helloooooooooooooooooooooooooo")
#         print(token)
#         user_activation_token = UserActivationToken.objects.create(user=user, token=token)
#         logger.debug(f"UserActivationToken created: {user_activation_token}")

#         subject = "Activate Your Account for Mando Website"
#         context = {
#             'frontend_url': settings.FRONTEND_URL,
#             'uid': user.pk,
#             'token': token,
#         }
#         email_body = render_to_string('courses/custom_activation_email.html', context)
#         plain_message = f"Activate your account by visiting this link: {context['frontend_url']}/activate/{context['uid']}/{context['token']}"

#         logger.debug(f"Email context: {context}")
#         logger.debug(f"Rendered HTML email body: {email_body}")

#         send_mail(
#             subject=subject,
#             message=plain_message,
#             html_message=email_body,
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[user.email],
#             fail_silently=False,
#         )
#         logger.info("Activation email sent successfully.")
        
#         return user

from rest_framework import serializers
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import User, UserActivationToken
import uuid
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
        fields = ['email', 'first_name', 'last_name', 'role', 'bio', 'website', 'profile_picture']

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