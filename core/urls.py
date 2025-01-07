
'''Newly created file'''

from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('csrf/', views.get_csrf_token, name='get_csrf_token'),
]