from django.urls import path, include
from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register('notifications', views.NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls))
]
