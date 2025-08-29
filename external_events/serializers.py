from rest_framework import serializers
from .models import ExternalEvent

class ExternalEventSerializer(serializers.ModelSerializer):
    is_past = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    
    class Meta:
        model = ExternalEvent
        fields = [
            'id', 'external_id', 'provider', 'title', 'description',
            'location', 'start_time', 'end_time', 'venue_name',
            'venue_address', 'image_url', 'ticket_url', 'price_range',
            'category', 'tags', 'fetched_at', 'is_imported',
            'is_past', 'is_upcoming'
        ]
        read_only_fields = [
            'external_id', 'provider', 'fetched_at', 'is_imported'
        ]

class ExternalEventImportSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    max_attendees = serializers.IntegerField(required=False, min_value=1)
    is_recurring = serializers.BooleanField(default=False)
    recurrence_pattern = serializers.CharField(required=False, allow_blank=True)

class ExternalEventSearchSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(
        choices=ExternalEvent.PROVIDER_CHOICES,
        required=False
    )
    query = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    sort_by = serializers.ChoiceField(
        choices=[
            ('start_time', 'Start Time'),
            ('title', 'Title'),
            ('fetched_at', 'Fetched At')
        ],
        default='start_time'
    )
    sort_order = serializers.ChoiceField(
        choices=[('asc', 'Ascending'), ('desc', 'Descending')],
        default='desc'
    )
