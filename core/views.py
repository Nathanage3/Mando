
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from djoser.views import UserViewSet
from django.shortcuts import render
from djoser.views import UserViewSet

class CustomUserViewSet(UserViewSet):
    def set_password(self, request, *args, **kwargs):
        try:
            response = super().set_password(request, *args, **kwargs)
            return response
        except KeyError as e:
            return JsonResponse({'error': str(e)}, status=400)
