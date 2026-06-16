from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Allow filtering by is_read query param
        queryset = Notification.objects.filter(recipient=self.request.user)
        is_read_param = self.request.query_params.get('is_read')
        if is_read_param is not None:
            is_read = is_read_param.lower() in ['true', '1']
            queryset = queryset.filter(is_read=is_read)
        return queryset

class NotificationMarkReadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, pk):
        notification = get_object_or_404(Notification, id=pk, recipient=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationMarkAllReadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({"message": "Toutes les notifications ont été marquées comme lues."}, status=status.HTTP_200_OK)

class NotificationUnreadCountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({"count": count}, status=status.HTTP_200_OK)
