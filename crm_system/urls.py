from django.contrib import admin
from django.urls import path, include
from crmapp import views as v
from crmapp.views import HomeView, ProfileView
from django.conf import settings
from crmapp.admin import admin_site
from django.conf.urls import handler403

handler403 = 'crmapp.views.custom_403_view'

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', v.custom_login, name='login'),
    path('crm_meet/', v.crm_meet_view, name='crm_meet'),
    path('logout/', v.custom_logout, name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('validate_login/', v.validate_login, name='validate_login'),
    path('register/', v.register, name='register'),
    path('home/', HomeView.as_view(), name='home'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('forgot-password/', v.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', v.reset_password, name='reset_password'),
    path('api/contacts/', v.get_contacts, name='get_contacts'),
    path('api/add_contact/', v.add_contact, name='add_contact'),
    path('api/save_data/', v.save_data, name='save_data'),
    path('meetings/', v.meeting_list, name='meeting_list'),
    path('check-username/', v.check_username, name='check_username'),
    path('check-email/', v.check_email, name='check_email'),
    path('fetch-meetings/', v.fetch_meetings, name='fetch_meetings'),
    path('create_meeting/', v.create_meeting, name='create_meeting'),
    path('get_upcoming_meetings/', v.get_upcoming_meetings, name='get_upcoming_meetings'),
    path('update_edit_meeting/<int:id>/', v.update_edit_meeting, name='update_edit_meeting'),
    path('delete_meeting/<int:meeting_id>/', v.delete_meeting, name='delete_meeting'),
]
