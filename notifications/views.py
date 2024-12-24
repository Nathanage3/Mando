from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Notification
from .serializers import NotificationSerializer, UpdateNotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter notifications for the authenticated user
        user = self.request.user
        if user.is_superuser:
            return Notification.objects.all()
        return Notification.objects.filter(user=user, read=False)
    
    def get_serializer_class(self):
        if self.action == 'mark_as_read':
            return UpdateNotificationSerializer
        return NotificationSerializer
    
    def perform_create(self, serializer):
        # Associate the notification with the authenticated user
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        serializer = self.get_serializer(
            notification,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            notification.read = True
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)