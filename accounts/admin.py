from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_organizer', 'bio', 'phone_number', 'profile_picture', 'get_full_name', 'email_verified', 'is_active')
    list_filter = ('is_organizer',)
    search_fields = ('username', 'email')
    ordering = ('username',)
