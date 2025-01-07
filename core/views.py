from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserCreateSerializer
from .tokens import account_activation_token
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from .models import User
import logging
import uuid

logger = logging.getLogger(__name__)


class CustomUserViewSet(UserViewSet):
    """
    Custom User ViewSet to handle additional user-related actions.
    Inherits from Djoser's UserViewSet.
    """

    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile_picture(self, request):
        """
        Custom action to update the user's profile picture.
        """
        try:
            user = request.user
            profile_picture = request.FILES.get('profile_picture')

            if not profile_picture:
                return Response({'error': 'No profile picture uploaded'}, status=400)

            # You could add additional validation for file type or size here
            user.profile_picture = profile_picture
            user.save()

            logger.info(f"Profile picture updated for {user.email}")
            return Response({'status': 'Profile picture updated successfully'}, status=200)

        except Exception as e:
            logger.error(f"Error updating profile picture: {str(e)}")
            return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def signup(request):
    """API endpoint for user registration."""
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.is_active = False  # Mark user as inactive until email verification
        user.save()

        # Generate activation token and UID
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        # Create activation link for the frontend
        activation_url = f"{settings.FRONTEND_URL}/activate/{uid}/{token}"

        # Send email to the user
        subject = "*Activate Your Account for Mando Site #2*"
        message = (
                    f"Hi {user.first_name},\n\n"
                    f"Please click the link below to activate your account:\n\n {activation_url}\n\n"
                    "If you did not register on our site, please ignore this message.\n"
                    "Best regards,\n\nMando Team"
                )

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email],
            )
            email.send()
            return Response(
                {'message': 'Account created. Check your email to activate your account.'},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            # Handle email sending failure
            user.delete()  # Rollback user creation if email fails
            return Response(
                {'error': f"Failed to send activation email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([AllowAny])
def activate(request, uidb64, token):
    """API endpoint for activating a user account."""
    from django.contrib.auth import get_user_model
    User = get_user_model()


    try:
        # Decode the UID from the base64 URL-safe format
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Invalid activation link'}, status=status.HTTP_400_BAD_REQUEST)

    # Verify the token
    if account_activation_token.check_token(user, token):
        user.is_active = True
        user.email_confirmed = True
        user.save()
        return Response({'message': 'Account activated successfully.'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def some_protected_view(request):
    if not request.user.email_confirmed:
        return Response({'error': 'Please verify your email address.'}, status=403)
    return Response({'message': 'Welcome!'})


@api_view(['GET'])
def get_csrf_token(request):
    csrf_token = get_token(request)
    return Response({'csrftoken': csrf_token})
