from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from .models import Report, Flag, Dispute, DisputeMessage
from products.models import Product
from accounts.models import Seller
from chats.models import Message, Chat

User = get_user_model()


class ReportSerializer(serializers.ModelSerializer):
    # Read-only fields for frontend display
    reported_item_id = serializers.CharField(read_only=True)
    reported_item_title = serializers.CharField(read_only=True)
    reporter_id = serializers.CharField(source='reporter.id', read_only=True)
    reporter_name = serializers.CharField(read_only=True)
    reporter_email = serializers.CharField(read_only=True)
    reported_user_id = serializers.CharField(source='reported_user.id', read_only=True)
    reported_user_name = serializers.CharField(read_only=True)
    
    # Write fields for creating reports
    reported_item_type = serializers.CharField(write_only=True, help_text="Type of item being reported")
    reported_item_object_id = serializers.CharField(write_only=True, help_text="ID of the item being reported")
    
    class Meta:
        model = Report
        fields = [
            'id', 'type', 'reported_item_id', 'reported_item_title',
            'reporter_id', 'reporter_name', 'reporter_email',
            'reported_user_id', 'reported_user_name',
            'reason', 'description', 'status', 'priority',
            'evidence_urls', 'admin_notes', 'resolution',
            'created_at', 'updated_at', 'resolved_at',
            # Write-only fields
            'reported_item_type', 'reported_item_object_id'
        ]
        read_only_fields = [
            'id', 'status', 'priority', 'admin_notes', 'resolution',
            'resolved_at', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        # Extract the write-only fields
        reported_item_type = validated_data.pop('reported_item_type')
        reported_item_object_id = validated_data.pop('reported_item_object_id')
        
        # Set the reporter to the current user
        validated_data['reporter'] = self.context['request'].user
        
        # Determine the content type and set the generic foreign key
        content_type_mapping = {
            'listing': ('products', 'product'),
            'seller': ('accounts', 'seller'),
            'message': ('chats', 'message'),
            'review': ('products', 'review'),  # Assuming you have a review model
        }
        
        if reported_item_type in content_type_mapping:
            app_label, model = content_type_mapping[reported_item_type]
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            validated_data['content_type'] = content_type
            validated_data['object_id'] = reported_item_object_id
            
            # Set reported_user based on the item type
            try:
                if reported_item_type == 'listing':
                    product = Product.objects.get(id=reported_item_object_id)
                    validated_data['reported_user'] = product.seller
                elif reported_item_type == 'seller':
                    seller = Seller.objects.get(id=reported_item_object_id)
                    validated_data['reported_user'] = seller.user
                elif reported_item_type == 'message':
                    message = Message.objects.get(id=reported_item_object_id)
                    validated_data['reported_user'] = message.sender
            except (Product.DoesNotExist, Seller.DoesNotExist, Message.DoesNotExist):
                pass  # reported_user will remain None
        
        return super().create(validated_data)


class ReportAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updates to reports"""
    class Meta:
        model = Report
        fields = [
            'status', 'priority', 'admin_notes', 'resolution', 'assigned_admin'
        ]
    
    def validate_assigned_admin(self, value):
        if value and not value.is_admin:
            raise serializers.ValidationError("Assigned admin must have admin role")
        return value


class FlagSerializer(serializers.ModelSerializer):
    # Read-only fields for frontend display
    item_id = serializers.CharField(read_only=True)
    item_title = serializers.CharField(read_only=True)
    
    # Write fields for creating flags
    flagged_item_type = serializers.CharField(write_only=True, help_text="Type of item being flagged")
    flagged_item_object_id = serializers.CharField(write_only=True, help_text="ID of the item being flagged")
    
    class Meta:
        model = Flag
        fields = [
            'id', 'item_type', 'item_id', 'item_title',
            'flag_type', 'reason', 'severity', 'status',
            'flagged_by', 'auto_actions_taken', 'manual_review_required',
            'admin_notes', 'flagged_at', 'reviewed_at',
            # Write-only fields
            'flagged_item_type', 'flagged_item_object_id'
        ]
        read_only_fields = [
            'id', 'flagged_at', 'reviewed_at'
        ]
    
    def create(self, validated_data):
        # Extract the write-only fields
        flagged_item_type = validated_data.pop('flagged_item_type')
        flagged_item_object_id = validated_data.pop('flagged_item_object_id')
        
        # Determine the content type and set the generic foreign key
        content_type_mapping = {
            'listing': ('products', 'product'),
            'seller': ('accounts', 'seller'),
            'review': ('products', 'review'),
            'user': ('accounts', 'customuser'),
        }
        
        if flagged_item_type in content_type_mapping:
            app_label, model = content_type_mapping[flagged_item_type]
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            validated_data['content_type'] = content_type
            validated_data['object_id'] = flagged_item_object_id
        
        # Set flagged_by_user if user is authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['flagged_by_user'] = request.user
            if validated_data.get('flag_type') == 'user_reported':
                validated_data['flagged_by'] = 'Community'
        
        return super().create(validated_data)


class FlagAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updates to flags"""
    class Meta:
        model = Flag
        fields = [
            'status', 'severity', 'admin_notes', 'reviewed_by', 'manual_review_required'
        ]
    
    def validate_reviewed_by(self, value):
        if value and not value.is_admin:
            raise serializers.ValidationError("Reviewer must have admin role")
        return value


class ReportsStatsSerializer(serializers.Serializer):
    """Serializer for reports and flags statistics"""
    total_reports = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    resolved_reports = serializers.IntegerField()
    dismissed_reports = serializers.IntegerField()
    total_flags = serializers.IntegerField()
    active_flags = serializers.IntegerField()
    critical_flags = serializers.IntegerField()
    avg_resolution_time = serializers.FloatField()


class ReportListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing reports"""
    reported_item_id = serializers.CharField(read_only=True)
    reported_item_title = serializers.CharField(read_only=True)
    reporter_name = serializers.CharField(read_only=True)
    reported_user_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'type', 'reported_item_id', 'reported_item_title',
            'reporter_name', 'reported_user_name', 'reason', 'status',
            'priority', 'created_at', 'updated_at'
        ]


class FlagListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing flags"""
    item_id = serializers.CharField(read_only=True)
    item_title = serializers.CharField(read_only=True)
    
    class Meta:
        model = Flag
        fields = [
            'id', 'item_type', 'item_id', 'item_title',
            'flag_type', 'reason', 'severity', 'status',
            'flagged_by', 'flagged_at', 'manual_review_required'
        ]


# Dispute Serializers

class DisputeMessageSerializer(serializers.ModelSerializer):
    """Serializer for dispute messages"""
    sender_name = serializers.SerializerMethodField()
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)
    is_own_message = serializers.SerializerMethodField()
    
    class Meta:
        model = DisputeMessage
        fields = [
            'id', 'message_type', 'content', 'attachments',
            'sender_name', 'sender_email', 'sender_role', 'is_own_message',
            'is_read_by_buyer', 'is_read_by_seller', 'is_read_by_admin',
            'is_edited', 'edited_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'sender_name', 'sender_email', 'sender_role', 'is_own_message',
            'is_read_by_buyer', 'is_read_by_seller', 'is_read_by_admin',
            'is_edited', 'edited_at', 'created_at'
        ]
    
    def get_sender_name(self, obj):
        if hasattr(obj.sender, 'profile') and obj.sender.profile.full_name:
            return obj.sender.profile.full_name
        return obj.sender.username or obj.sender.email
    
    def get_is_own_message(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user
        return False


class DisputeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing disputes"""
    buyer_name = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    admin_name = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Dispute
        fields = [
            'id', 'title', 'status', 'is_resolved', 'admin_joined',
            'buyer_name', 'seller_name', 'product_name', 'admin_name',
            'unread_messages_count', 'participants_count',
            'created_at', 'last_message_at', 'resolved_at'
        ]
    
    def get_buyer_name(self, obj):
        if hasattr(obj.buyer, 'profile') and obj.buyer.profile.full_name:
            return obj.buyer.profile.full_name
        return obj.buyer.username or obj.buyer.email
    
    def get_seller_name(self, obj):
        if hasattr(obj.seller, 'profile') and obj.seller.profile.full_name:
            return obj.seller.profile.full_name
        return obj.seller.username or obj.seller.email
    
    def get_admin_name(self, obj):
        if obj.admin_user:
            if hasattr(obj.admin_user, 'profile') and obj.admin_user.profile.full_name:
                return obj.admin_user.profile.full_name
            return obj.admin_user.username or obj.admin_user.email
        return None
    
    def get_unread_messages_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        user = request.user
        unread_filter = {}
        
        if user == obj.buyer:
            unread_filter['is_read_by_buyer'] = False
        elif user == obj.seller:
            unread_filter['is_read_by_seller'] = False
        elif user == obj.admin_user:
            unread_filter['is_read_by_admin'] = False
        else:
            return 0
        
        return obj.messages.filter(**unread_filter).exclude(sender=user).count()
    
    def get_participants_count(self, obj):
        return len(obj.participants)


class DisputeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for dispute with all information"""
    buyer_info = serializers.SerializerMethodField()
    seller_info = serializers.SerializerMethodField()
    admin_info = serializers.SerializerMethodField()
    product_info = serializers.SerializerMethodField()
    messages = DisputeMessageSerializer(many=True, read_only=True)
    participants_online_status = serializers.SerializerMethodField()
    can_resolve = serializers.SerializerMethodField()
    can_join_as_admin = serializers.SerializerMethodField()
    escalated_chat_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Dispute
        fields = [
            'id', 'title', 'description', 'status', 'is_resolved',
            'resolution_type', 'resolution_description', 'admin_decision',
            'admin_joined', 'buyer_marked_resolved', 'seller_marked_resolved',
            'buyer_info', 'seller_info', 'admin_info', 'product_info',
            'evidence_urls', 'messages', 'participants_online_status',
            'can_resolve', 'can_join_as_admin', 'escalated_chat_info',
            'created_at', 'updated_at', 'resolved_at', 'last_message_at'
        ]
        read_only_fields = [
            'id', 'is_resolved', 'resolution_type', 'resolved_at',
            'buyer_marked_resolved', 'seller_marked_resolved',
            'admin_joined', 'messages', 'created_at', 'updated_at', 'last_message_at'
        ]
    
    def get_buyer_info(self, obj):
        return {
            'id': str(obj.buyer.id),
            'email': obj.buyer.email,
            'name': self._get_user_name(obj.buyer),
            'role': obj.buyer.role,
            'is_online': False  # TODO: Implement online status
        }
    
    def get_seller_info(self, obj):
        return {
            'id': str(obj.seller.id),
            'email': obj.seller.email,
            'name': self._get_user_name(obj.seller),
            'role': obj.seller.role,
            'is_online': False  # TODO: Implement online status
        }
    
    def get_admin_info(self, obj):
        if obj.admin_user:
            return {
                'id': str(obj.admin_user.id),
                'email': obj.admin_user.email,
                'name': self._get_user_name(obj.admin_user),
                'role': obj.admin_user.role,
                'is_online': False  # TODO: Implement online status
            }
        return None
    
    def get_product_info(self, obj):
        if obj.product:
            # Use primary_image_url property which handles both ProductImage and legacy_images
            image_url = obj.product.primary_image_url
            return {
                'id': str(obj.product.id),
                'name': obj.product.name,
                'price': str(obj.product.price),
                'image_url': image_url
            }
        return None
    
    def get_participants_online_status(self, obj):
        # TODO: Implement real online status tracking
        return {
            'buyer_online': False,
            'seller_online': False,
            'admin_online': False if not obj.admin_user else False
        }
    
    def get_can_resolve(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        if obj.is_resolved:
            return False
        
        # Admin can always resolve
        if user.is_admin:
            return True
        
        # Participants can mark as resolved (but not actually resolve until both agree)
        return user in [obj.buyer, obj.seller]
    
    def get_can_join_as_admin(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return request.user.is_admin and not obj.admin_joined
    
    def get_escalated_chat_info(self, obj):
        if obj.escalated_from_chat:
            return {
                'id': str(obj.escalated_from_chat.id),
                'created_at': obj.escalated_from_chat.created_at
            }
        return None
    
    def _get_user_name(self, user):
        if hasattr(user, 'profile') and user.profile.full_name:
            return user.profile.full_name
        return user.username or user.email


class DisputeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new disputes"""
    escalate_from_chat_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Dispute
        fields = [
            'title', 'description', 'product', 'evidence_urls',
            'escalate_from_chat_id'
        ]
    
    def validate_escalate_from_chat_id(self, value):
        if value:
            try:
                chat = Chat.objects.get(id=value)
                # Verify user is part of the chat
                request = self.context.get('request')
                if request and request.user.is_authenticated:
                    if request.user not in [chat.buyer, chat.seller]:
                        raise serializers.ValidationError("You are not a participant in this chat")
                return value
            except Chat.DoesNotExist:
                raise serializers.ValidationError("Chat does not exist")
        return value
    
    def create(self, validated_data):
        escalate_from_chat_id = validated_data.pop('escalate_from_chat_id', None)
        request = self.context['request']
        user = request.user
        
        if escalate_from_chat_id:
            # Escalating from existing chat
            chat = Chat.objects.get(id=escalate_from_chat_id)
            validated_data['buyer'] = chat.buyer
            validated_data['seller'] = chat.seller
            validated_data['product'] = chat.product
            validated_data['escalated_from_chat'] = chat
        else:
            # Creating new dispute - need to determine buyer/seller
            product = validated_data.get('product')
            if product:
                if user == product.seller:
                    raise serializers.ValidationError("Seller cannot create dispute against themselves")
                validated_data['buyer'] = user
                validated_data['seller'] = product.seller
            else:
                raise serializers.ValidationError("Product is required for new disputes")
        
        return super().create(validated_data)


class DisputeMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating dispute messages"""
    
    class Meta:
        model = DisputeMessage
        fields = ['message_type', 'content', 'attachments']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        validated_data['dispute'] = self.context['dispute']
        return super().create(validated_data)


class DisputeResolveSerializer(serializers.Serializer):
    """Serializer for resolving disputes"""
    resolution_description = serializers.CharField(required=False, allow_blank=True)
    admin_decision = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        request = self.context.get('request')
        dispute = self.context.get('dispute')
        
        if not request or not dispute:
            raise serializers.ValidationError("Invalid context")
        
        user = request.user
        
        # If admin is resolving, require admin_decision
        if user.is_admin and not data.get('admin_decision'):
            raise serializers.ValidationError("Admin decision is required when admin resolves dispute")
        
        return data
