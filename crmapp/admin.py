from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Contact, Profile, Meeting

# Custom AdminSite class
class CustomAdminSite(admin.AdminSite):
    site_header = 'CRM APP'
    site_title = 'CRM APP'
    index_title = 'CRM APP Dashboard'

# Instantiate the custom admin site
admin_site = CustomAdminSite(name='custom_admin')

# Register your models with the custom admin site
@admin.register(Contact, site=admin_site)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number')
    search_fields = ('name', 'phone_number')
    list_display_links = ('name',)

@admin.register(Profile, site=admin_site)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'date_of_birth', 'facebook', 'twitter', 'linkedin', 'instagram')
    search_fields = ('user__username', 'phone_number', 'facebook', 'twitter', 'linkedin', 'instagram')
    list_filter = ('date_of_birth',)
    readonly_fields = ('user',)

@admin.register(Meeting, site=admin_site)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('contact', 'platform', 'status', 'more', 'date', 'meetup_time', 'message', 'link')
    search_fields = ('contact__name', 'platform', 'status', 'message')
    list_filter = ('platform', 'status', 'date')
    ordering = ('-date',)
    
    actions = ['mark_as_completed']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
    mark_as_completed.short_description = "Mark selected meetings as completed"
