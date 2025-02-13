
'''Newly created file'''
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet
from . import views

router = DefaultRouter()
router.register(r'auth/users', CustomUserViewSet, basename='user')

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('csrf/', views.get_csrf_token, name='get_csrf_token'),
    path('reset-password/', views.reset_password_request, name='reset-password-request'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_confirm, name='reset-password-confirm'),
    path('', include(router.urls)),  # This line includes the router URLs
]
