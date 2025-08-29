from rest_framework import serializers
from .models import RSVP
from accounts.serializers import UserSerializer
from events.serializers import EventSerializer

class RSVPSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    
    class Meta:
        model = RSVP
        fields = ['id', 'user', 'event', 'status', 'created_at', 'updated_at']
        read_only_fields = ['user', 'event', 'created_at', 'updated_at']

class RSVPCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSVP
        fields = ['status']
    
    def create(self, validated_data):
        user = self.context['request'].user
        event_id = self.context['event_id']
        
        # Check if RSVP already exists
        rsvp, created = RSVP.objects.get_or_create(
            user=user,
            event_id=event_id,
            defaults={'status': validated_data['status']}
        )
        
        if not created:
            # Update existing RSVP
            rsvp.status = validated_data['status']
            rsvp.save()
        
        return rsvp

class AttendeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = RSVP
        fields = ['id', 'user', 'status', 'created_at']
