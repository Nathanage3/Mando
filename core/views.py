# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from djoser.views import UserViewSet
# from django.http import JsonResponse

# class CustomUserViewSet(UserViewSet):
#     """
#     Custom User ViewSet to handle additional user-related actions.
#     Inherits from Djoser's UserViewSet.
#     """

#     def set_password(self, request, *args, **kwargs):
#         """
#         Override Djoser's set_password to handle custom exceptions.
#         """
#         try:
#             response = super().set_password(request, *args, **kwargs)
#             return response
#         except KeyError as e:
#             return JsonResponse({'error': str(e)}, status=400)

#     @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
#     def update_profile_picture(self, request):
#         """
#         Custom action to update the user's profile picture.
#         """
#         try:
#             # Fetch the authenticated user
#             user = request.user

#             # Check if 'profile_picture' is in the uploaded files
#             profile_picture = request.FILES.get('profile_picture')
#             if not profile_picture:
#                 return Response({'error': 'No profile picture uploaded'}, status=400)

#             # Update the profile picture
#             user.profile_picture = profile_picture
#             user.save()

#             return Response({'status': 'Profile picture updated successfully'}, status=200)

#         except Exception as e:
#             return Response({'error': str(e)}, status=500)
        
# # core/views.py

# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.decorators import api_view
# from django.contrib.auth.models import User
# from django.db import transaction
# from courses.models import UserActivationToken
# from courses.emails import send_activation_email  # Import the email utility function
# import logging

# logger = logging.getLogger(__name__)


# @api_view(['POST'])
# def create_user(request):
#     """
#     API endpoint to create a user and return the activation token.
#     """
#     try:
#         with transaction.atomic():
#             # Extract user data from request
#             email = request.data.get('email')
#             password = request.data.get('password')

#             # Validate required fields
#             if not all([email, password]):
#                 return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

#             # Create the user
#             user = User.objects.create_user(email=email, password=password)

#             # Generate the activation token
#             activation_token, created = UserActivationToken.objects.get_or_create(user=user)

#             # Send activation email
#             send_activation_email(user, activation_token.token)

#             # Return response to frontend
#             return Response({
#                 "message": "User created successfully. Activation email sent.",
#                 "user_id": user.id,
#                 "activation_token": str(activation_token.token),
#                 "email": user.email
#             }, status=status.HTTP_201_CREATED)
#     except Exception as e:
#         logger.error(f"Error creating user: {str(e)}")
#         return Response({"error": "Failed to create user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from djoser.views import UserViewSet
from django.http import JsonResponse
from .models import UserActivationToken
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import logging
import uuid

logger = logging.getLogger(__name__)

class CustomUserViewSet(UserViewSet):
    """
    Custom User ViewSet to handle additional user-related actions.
    Inherits from Djoser's UserViewSet.
    """

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @csrf_exempt
    def reset_password(self, request):
        # Your custom password reset logic here (if any)
        pass

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
        
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def create_activation_token(self, request):
        try:
            user = request.user
            # Invalidate existing token if it exists
            UserActivationToken.objects.filter(user=user).delete()

            # Generate new token
            activation_token = UserActivationToken.objects.create(user=user)

            return Response({
                "message": "Activation token created successfully.",
                "activation_token": str(activation_token.token),
            }, status=201)
        except Exception as e:
            logger.error(f"Error creating activation token: {e}")
            return Response({'error': 'Failed to create activation token'}, status=500)
        
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import UserActivationToken, User
import logging

# Configure logger
logger = logging.getLogger(__name__)

def verify_email(request, token):
    uid = request.GET.get('uid')
   
    if not uid:
        return JsonResponse({'error': "User ID ('uid') is required."}, status=400)

    try:
        uid = int(uid.strip('/'))
        user = get_object_or_404(User, pk=uid)

        user_activation_token = get_object_or_404(UserActivationToken, user=user, token=token)
        user.is_active = True
        user.save()
        """Uncomment this line if the token is useful after login"""
        #user_activation_token.delete()
    
        return HttpResponse("Email verified successfully.", status=200)

    except ValueError as e:
        return JsonResponse({'error': "'uid' must be a valid integer."}, status=400)

    except User.DoesNotExist:
        return JsonResponse({'error': "User not found."}, status=404)

    except UserActivationToken.DoesNotExist:
        return JsonResponse({'error': "Invalid token or activation token not found."}, status=404)

    except Exception as e:
        return JsonResponse({'error': "An unexpected error occurred."}, status=500)
