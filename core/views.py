
# from django.contrib.auth import views as auth_views
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated, IsAdminUser
# from rest_framework.viewsets import ModelViewSet
# from django.http import JsonResponse
# from djoser.views import UserViewSet
# from django.shortcuts import render
# from .models import User
# from djoser.views import UserViewSet
# from .serializers import UserSerializer

'''
class CustomUserViewSet(UserViewSet):
    def set_password(self, request, *args, **kwargs):
        try:
            response = super().set_password(request, *args, **kwargs)
            return response
        except KeyError as e:
            return JsonResponse({'error': str(e)}, status=400)
        

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['PUT'], permission_classes=[IsAuthenticated])
    def update_profile_picture(self, request):
        try:
            # Fetch the authenticated user
            user = request.user

            # Check if 'profile_picture' is in the uploaded files
            profile_picture = request.FILES.get('profile_picture')
            if not profile_picture:
                return Response({'error': 'No profile picture uploaded'}, status=400)

            # Update the profile picture
            user.profile_picture = profile_picture
            user.save()

            return Response({'status': 'Profile picture updated successfully'}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)
'''

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from django.http import JsonResponse

class CustomUserViewSet(UserViewSet):
    """
    Custom User ViewSet to handle additional user-related actions.
    Inherits from Djoser's UserViewSet.
    """

    def set_password(self, request, *args, **kwargs):
        """
        Override Djoser's set_password to handle custom exceptions.
        """
        try:
            response = super().set_password(request, *args, **kwargs)
            return response
        except KeyError as e:
            return JsonResponse({'error': str(e)}, status=400)

    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile_picture(self, request):
        """
        Custom action to update the user's profile picture.
        """
        try:
            # Fetch the authenticated user
            user = request.user

            # Check if 'profile_picture' is in the uploaded files
            profile_picture = request.FILES.get('profile_picture')
            if not profile_picture:
                return Response({'error': 'No profile picture uploaded'}, status=400)

            # Update the profile picture
            user.profile_picture = profile_picture
            user.save()

            return Response({'status': 'Profile picture updated successfully'}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)
