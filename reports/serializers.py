from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from .models import Report, Flag
from products.models import Product
from accounts.models import Seller
from chats.models import Message

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
