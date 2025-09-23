from django.shortcuts import render
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Report, Flag, Dispute, DisputeMessage
from .serializers import (
    ReportSerializer, ReportAdminUpdateSerializer, ReportListSerializer,
    FlagSerializer, FlagAdminUpdateSerializer, FlagListSerializer,
    ReportsStatsSerializer, DisputeListSerializer, DisputeDetailSerializer,
    DisputeCreateSerializer, DisputeMessageSerializer, DisputeMessageCreateSerializer,
    DisputeResolveSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    Regular users can create reports but only view their own.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return True
        
        # For reports, users can only view their own submissions
        if isinstance(obj, Report):
            return obj.reporter == request.user
        
        # For flags, only admins can view/edit
        if isinstance(obj, Flag):
            return hasattr(request.user, 'is_admin') and request.user.is_admin
        
        return False


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   hasattr(request.user, 'is_admin') and request.user.is_admin)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling reports.
    - Users can create and view their own reports
    - Admins can view/update all reports
    """
    queryset = Report.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'type', 'reason']
    search_fields = ['description', 'reported_item_title', 'reporter_name']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ReportListSerializer
        elif self.action in ['update', 'partial_update'] and self.request.user.is_admin:
            return ReportAdminUpdateSerializer
        return ReportSerializer

    def get_queryset(self):
        queryset = Report.objects.all()
        
        # Regular users can only see their own reports
        if not (hasattr(self.request.user, 'is_admin') and self.request.user.is_admin):
            queryset = queryset.filter(reporter=self.request.user)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    def update(self, request, *args, **kwargs):
        # Only admins can update reports
        if not (hasattr(request.user, 'is_admin') and request.user.is_admin):
            return Response(
                {"detail": "You don't have permission to update reports."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Set resolved_at when status changes to resolved
        if 'status' in serializer.validated_data:
            if serializer.validated_data['status'] == 'resolved':
                serializer.save(resolved_at=timezone.now())
            else:
                serializer.save()
        else:
            serializer.save()
        
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_reports(self, request):
        """Get reports submitted by the current user"""
        reports = self.get_queryset().filter(reporter=request.user)
        serializer = ReportListSerializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """Get all pending reports (admin only)"""
        reports = self.get_queryset().filter(status='pending')
        serializer = ReportListSerializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def assign(self, request, pk=None):
        """Assign report to an admin"""
        report = self.get_object()
        admin_id = request.data.get('admin_id')
        
        if admin_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                admin_user = User.objects.get(id=admin_id, role='admin')
                report.assigned_admin = admin_user
                report.save()
                return Response({"detail": "Report assigned successfully"})
            except User.DoesNotExist:
                return Response(
                    {"detail": "Admin user not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            report.assigned_admin = None
            report.save()
            return Response({"detail": "Report unassigned"})


class FlagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling flags.
    - Only admins can view/manage flags
    - System can create automated flags
    """
    queryset = Flag.objects.all()
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'severity', 'item_type', 'flag_type']
    search_fields = ['reason', 'item_title', 'admin_notes']
    ordering_fields = ['flagged_at', 'reviewed_at', 'severity']
    ordering = ['-flagged_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return FlagListSerializer
        elif self.action in ['update', 'partial_update']:
            return FlagAdminUpdateSerializer
        return FlagSerializer

    def perform_update(self, serializer):
        # Set reviewed_at when status changes from active
        if 'status' in serializer.validated_data:
            if (serializer.validated_data['status'] in ['resolved', 'ignored'] and 
                self.get_object().status == 'active'):
                serializer.save(
                    reviewed_at=timezone.now(),
                    reviewed_by=self.request.user
                )
            else:
                serializer.save()
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active flags"""
        flags = self.get_queryset().filter(status='active')
        serializer = FlagListSerializer(flags, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Get all critical severity flags"""
        flags = self.get_queryset().filter(severity='critical')
        serializer = FlagListSerializer(flags, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def requires_review(self, request):
        """Get all flags that require manual review"""
        flags = self.get_queryset().filter(manual_review_required=True, status='active')
        serializer = FlagListSerializer(flags, many=True)
        return Response(serializer.data)


class ReportsStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for reports and flags statistics
    """
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get comprehensive stats for admin dashboard"""
        
        # Reports stats
        total_reports = Report.objects.count()
        pending_reports = Report.objects.filter(status='pending').count()
        resolved_reports = Report.objects.filter(status='resolved').count()
        dismissed_reports = Report.objects.filter(status='dismissed').count()
        
        # Flags stats
        total_flags = Flag.objects.count()
        active_flags = Flag.objects.filter(status='active').count()
        critical_flags = Flag.objects.filter(severity='critical', status='active').count()
        
        # Average resolution time (in days)
        resolved_reports_with_time = Report.objects.filter(
            status='resolved',
            resolved_at__isnull=False
        )
        
        avg_resolution_time = 0
        if resolved_reports_with_time.exists():
            # Calculate average resolution time in days
            total_time = sum(
                (report.resolved_at - report.created_at).total_seconds() 
                for report in resolved_reports_with_time
            )
            avg_resolution_time = total_time / resolved_reports_with_time.count() / 86400  # Convert to days
        
        stats_data = {
            'total_reports': total_reports,
            'pending_reports': pending_reports,
            'resolved_reports': resolved_reports,
            'dismissed_reports': dismissed_reports,
            'total_flags': total_flags,
            'active_flags': active_flags,
            'critical_flags': critical_flags,
            'avg_resolution_time': round(avg_resolution_time, 1)
        }
        
        serializer = ReportsStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trends data for the last 30 days"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Reports by day
        reports_by_day = Report.objects.filter(
            created_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        # Flags by day
        flags_by_day = Flag.objects.filter(
            flagged_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(flagged_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return Response({
            'reports_by_day': list(reports_by_day),
            'flags_by_day': list(flags_by_day)
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary stats by category"""
        
        # Reports by type
        reports_by_type = Report.objects.values('type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Reports by reason
        reports_by_reason = Report.objects.values('reason').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Flags by item type
        flags_by_type = Flag.objects.values('item_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Flags by severity
        flags_by_severity = Flag.objects.values('severity').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'reports_by_type': list(reports_by_type),
            'reports_by_reason': list(reports_by_reason),
            'flags_by_type': list(flags_by_type),
            'flags_by_severity': list(flags_by_severity)
        })


class IsDisputeParticipant(permissions.BasePermission):
    """
    Custom permission to only allow dispute participants or admins to access disputes.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access all disputes
        if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return True
        
        # Participants can access their disputes
        if request.user in [obj.buyer, obj.seller]:
            return True
        
        # Admin who joined the dispute can access
        if obj.admin_joined and obj.admin_user == request.user:
            return True
        
        return False


class DisputeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling disputes between buyers and sellers.
    """
    queryset = Dispute.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsDisputeParticipant]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_resolved', 'admin_joined']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'last_message_at']
    ordering = ['-last_message_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return DisputeListSerializer
        elif self.action == 'create':
            return DisputeCreateSerializer
        elif self.action in ['resolve_dispute', 'mark_resolved']:
            return DisputeResolveSerializer
        return DisputeDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            # Admins can see all disputes
            return Dispute.objects.all()
        else:
            # Users can only see disputes they're involved in
            return Dispute.objects.filter(
                Q(buyer=user) | Q(seller=user) | 
                (Q(admin_joined=True) & Q(admin_user=user))
            )

    def create(self, request, *args, **kwargs):
        """Create a new dispute or escalate from chat"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user is trying to escalate from chat
        escalate_from_chat_id = serializer.validated_data.get('escalate_from_chat_id')
        if escalate_from_chat_id:
            # Verify no existing dispute for this chat
            from chats.models import Chat
            chat = Chat.objects.get(id=escalate_from_chat_id)
            if Dispute.objects.filter(escalated_from_chat=chat).exists():
                return Response(
                    {"detail": "A dispute already exists for this chat"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        dispute = serializer.save()
        
        # Create initial system message
        DisputeMessage.objects.create(
            dispute=dispute,
            sender=request.user,
            message_type='system',
            content=f"Dispute created by {self._get_user_name(request.user)}"
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            DisputeDetailSerializer(dispute, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in the dispute"""
        dispute = self.get_object()
        
        # Check if dispute is closed
        if dispute.is_resolved:
            return Response(
                {"detail": "Cannot send messages to resolved disputes"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user is a participant
        if request.user not in dispute.participants:
            return Response(
                {"detail": "You are not a participant in this dispute"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DisputeMessageCreateSerializer(
            data=request.data,
            context={'request': request, 'dispute': dispute}
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        
        # Send WebSocket notification
        self._notify_dispute_group(dispute, 'dispute_message', {
            'message': DisputeMessageSerializer(message, context={'request': request}).data
        })
        
        return Response(
            DisputeMessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def join_as_admin(self, request, pk=None):
        """Allow admin to join the dispute"""
        dispute = self.get_object()
        
        if dispute.admin_joined:
            return Response(
                {"detail": "An admin has already joined this dispute"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dispute.join_admin(request.user)
        
        # Send WebSocket notification
        self._notify_dispute_group(dispute, 'admin_joined', {
            'admin_name': self._get_user_name(request.user),
            'message': f'Buildmart admin {self._get_user_name(request.user)} just joined the chat'
        })
        
        return Response(
            {"detail": "Successfully joined the dispute as admin"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark dispute as resolved by participant"""
        dispute = self.get_object()
        user = request.user
        
        if dispute.is_resolved:
            return Response(
                {"detail": "Dispute is already resolved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only participants can mark as resolved
        if user not in [dispute.buyer, dispute.seller]:
            return Response(
                {"detail": "Only dispute participants can mark as resolved"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark user's resolution status
        if user == dispute.buyer:
            dispute.buyer_marked_resolved = True
        elif user == dispute.seller:
            dispute.seller_marked_resolved = True
        
        dispute.save()
        
        # Check if both parties agreed to resolve
        if dispute.can_be_resolved_mutually:
            serializer = DisputeResolveSerializer(
                data=request.data,
                context={'request': request, 'dispute': dispute}
            )
            serializer.is_valid(raise_exception=True)
            
            dispute.resolution_description = serializer.validated_data.get('resolution_description', '')
            dispute.mark_resolved_mutually()
            
            # Create system message
            DisputeMessage.objects.create(
                dispute=dispute,
                sender=user,
                message_type='system',
                content="Dispute resolved by mutual agreement"
            )
        else:
            # Create notification message
            other_party = dispute.seller if user == dispute.buyer else dispute.buyer
            DisputeMessage.objects.create(
                dispute=dispute,
                sender=user,
                message_type='system',
                content=f"{self._get_user_name(user)} marked this dispute as resolved. Waiting for {self._get_user_name(other_party)} to agree."
            )
        
        return Response(
            DisputeDetailSerializer(dispute, context={'request': request}).data
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def resolve_dispute(self, request, pk=None):
        """Admin resolves the dispute with a decision"""
        dispute = self.get_object()
        
        if dispute.is_resolved:
            return Response(
                {"detail": "Dispute is already resolved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DisputeResolveSerializer(
            data=request.data,
            context={'request': request, 'dispute': dispute}
        )
        serializer.is_valid(raise_exception=True)
        
        admin_decision = serializer.validated_data['admin_decision']
        dispute.mark_resolved_by_admin(request.user, admin_decision)
        
        # Create system message
        DisputeMessage.objects.create(
            dispute=dispute,
            sender=request.user,
            message_type='system',
            content=f"Dispute resolved by admin. Decision: {admin_decision}"
        )
        
        return Response(
            DisputeDetailSerializer(dispute, context={'request': request}).data
        )

    @action(detail=True, methods=['post'])
    def mark_messages_read(self, request, pk=None):
        """Mark all messages as read for the current user"""
        dispute = self.get_object()
        user = request.user
        
        # Get unread messages for this user
        for message in dispute.messages.all():
            message.mark_read_by_user(user)
        
        return Response({"detail": "Messages marked as read"})

    @action(detail=False, methods=['get'])
    def my_disputes(self, request):
        """Get disputes involving the current user"""
        user = request.user
        disputes = self.get_queryset().filter(
            Q(buyer=user) | Q(seller=user)
        )
        serializer = DisputeListSerializer(disputes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def admin_view(self, request):
        """Get all disputes for admin overview"""
        disputes = Dispute.objects.all()
        serializer = DisputeListSerializer(disputes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending_admin_action(self, request):
        """Get disputes that need admin attention"""
        disputes = Dispute.objects.filter(
            status__in=['open', 'in_progress'],
            admin_joined=False
        )
        serializer = DisputeListSerializer(disputes, many=True, context={'request': request})
        return Response(serializer.data)

    def _get_user_name(self, user):
        """Helper method to get user display name"""
        if hasattr(user, 'profile') and user.profile.full_name:
            return user.profile.full_name
        return user.username or user.email
    
    def _notify_dispute_group(self, dispute, event_type, data):
        """Send WebSocket notification to dispute group"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f'dispute_{dispute.id}'
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': event_type,
                    **data
                }
            )


class DisputeMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reading dispute messages
    """
    queryset = DisputeMessage.objects.all()
    serializer_class = DisputeMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['message_type', 'sender']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        dispute_id = self.kwargs.get('dispute_pk')
        if dispute_id:
            # Check if user has access to this dispute
            try:
                dispute = Dispute.objects.get(id=dispute_id)
                if self.request.user in dispute.participants or self.request.user.is_admin:
                    return DisputeMessage.objects.filter(dispute=dispute)
            except Dispute.DoesNotExist:
                pass
        
        return DisputeMessage.objects.none()
