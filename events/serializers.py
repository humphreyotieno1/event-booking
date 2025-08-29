from rest_framework import serializers
from .models import Event, EventCategory, EventTag, Review
from accounts.serializers import UserSerializer

class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'description']

class EventTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTag
        fields = ['id', 'name']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']

class EventSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    category = EventCategorySerializer(read_only=True)
    tags = EventTagSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    current_attendee_count = serializers.ReadOnlyField()
    available_spots = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'location', 'start_time', 'end_time',
            'created_by', 'max_attendees', 'external_event_id', 'category',
            'tags', 'is_recurring', 'recurrence_pattern', 'created_at',
            'updated_at', 'current_attendee_count', 'available_spots',
            'is_full', 'is_past', 'average_rating', 'reviews'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class EventCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'location', 'start_time', 'end_time',
            'max_attendees', 'category_id', 'tag_ids', 'is_recurring',
            'recurrence_pattern'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        category_id = validated_data.pop('category_id', None)
        
        # Set the created_by user
        validated_data['created_by'] = self.context['request'].user
        
        # Set category if provided
        if category_id:
            try:
                category = EventCategory.objects.get(id=category_id)
                validated_data['category'] = category
            except EventCategory.DoesNotExist:
                pass
        
        # Create the event
        event = Event.objects.create(**validated_data)
        
        # Add tags if provided
        if tag_ids:
            tags = EventTag.objects.filter(id__in=tag_ids)
            event.tags.set(tags)
        
        return event
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        category_id = validated_data.pop('category_id', None)
        
        # Update category if provided
        if category_id is not None:
            if category_id:
                try:
                    category = EventCategory.objects.get(id=category_id)
                    validated_data['category'] = category
                except EventCategory.DoesNotExist:
                    validated_data['category'] = None
            else:
                validated_data['category'] = None
        
        # Update the event
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_ids is not None:
            tags = EventTag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)
        
        return instance

class EventSearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, help_text="Search query")
    category_id = serializers.IntegerField(required=False)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    location = serializers.CharField(required=False)
    organizer_id = serializers.IntegerField(required=False)
    sort_by = serializers.ChoiceField(
        choices=[
            ('start_time', 'Start Time'),
            ('title', 'Title'),
            ('popularity', 'Popularity'),
            ('created_at', 'Created At')
        ],
        default='start_time'
    )
    sort_order = serializers.ChoiceField(
        choices=[('asc', 'Ascending'), ('desc', 'Descending')],
        default='desc'
    )
