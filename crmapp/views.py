import calendar
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.contrib.auth import logout, authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from crmapp.forms import SignUpForm, MeetingForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.contrib.auth.forms import SetPasswordForm
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from .models import Profile, Contact, Meeting
from datetime import datetime
import json
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
from django.db.models import Q

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['years'] = list(range(2024, 2026))
        context['months'] = [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]
        context['days'] = list(range(1, 32))
        context['contacts'] = Contact.objects.all().values('id', 'name', 'phone_number')
        context['meetings'] = Meeting.objects.all().select_related('contact')
        return context
    

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        user = self.request.user
        profile, created = Profile.objects.get_or_create(user=user)
        context = {
            'user': user,
            'profile': profile,
        }
        return context

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                form.add_error('email', 'This email address is already registered.')
                return render(request, 'register.html', {'form': form})

            user = form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SignUpForm()
    
    return render(request, 'register.html', {'form': form})

def validate_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({})
        else:
            return JsonResponse({'error': 'Invalid username or password.'}, status=400)
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to the home page or another page
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

    

def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('/')
    return HttpResponseForbidden("Method not allowed")


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        users = User.objects.filter(email=email)
        
        if not users.exists():
            messages.error(request, 'No user found with this email address.')
        else:
            for user in users:
                subject = 'Password Reset Request'
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = request.build_absolute_uri(reverse('reset_password', kwargs={'uidb64': uid, 'token': token}))
                context = {
                    'email': user.email,
                    'domain': request.get_host(),
                    'site_name': 'Your Site Name',
                    'uid': uid,
                    'user': user,
                    'token': token,
                    'protocol': 'http',  # Change to 'https' if using SSL
                }
                plain_message = render_to_string('password_reset_email.txt', context)
                html_message = render_to_string('password_reset_email.html', context)
                
                email_message = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email]
                )
                email_message.attach_alternative(html_message, "text/html")
                email_message.send()
            messages.success(request, 'Password reset email has been sent.')
        return redirect('forgot_password')
    
    return render(request, 'forgot_password.html')

def reset_password(request, uidb64=None, token=None):
    print(f'UID: {uidb64}')
    print(f'Token: {token}')

User = get_user_model()

def reset_password(request, uidb64, token):
    if request.method == 'POST':
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Password has been reset successfully.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
        else:
            messages.error(request, 'The link is invalid or has expired.')

        return redirect('forgot_password')

    return render(request, 'reset_password.html', {'uid': uidb64, 'token': token})


@login_required
@csrf_exempt
def save_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            platform = data.get('platform')
            status = data.get('status')
            more = data.get('more')
            year = int(data.get('year', 0))  
            month = int(data.get('month', 0))  
            day = int(data.get('day', 0))  
            contact_id = int(data.get('contact', 0))  
            meetup_time_str = data.get('meetup_time')

            if not all([platform, status, more, year, month, day, contact_id, meetup_time_str]):
                return JsonResponse({'success': False, 'error': 'Missing fields in the request'})

            contact = Contact.objects.get(id=contact_id)
            date = datetime(year, month, day).date()
            meetup_time = datetime.strptime(meetup_time_str, '%H:%M').time()

            # Check for duplicates
            if Meeting.objects.filter(
                contact=contact,
                platform=platform,
                status=status,
                more=more,
                date=date,
                meetup_time=meetup_time
            ).exists():
                return JsonResponse({'success': False, 'error': 'Duplicate meeting exists'})

            # Construct the link based on the selected platform
            if platform == 'Instagram':
                link = f'https://instagram.com/{contact.name}'
            elif platform == 'Facebook':
                link = f'https://facebook.com/{contact.name}'
            elif platform == 'LinkedIn':
                link = f'https://linkedin.com/in/{contact.name}'
            elif platform == 'Whatsapp':
                link = f'http://wa.me/91{contact.phone_number}'
            else:
                link = '#'

            meeting = Meeting(
                contact=contact,
                platform=platform,
                status=status,
                more=more,
                date=date,
                meetup_time=meetup_time,
                message=f'Hooray! The meet has been set for {year}-{str(month).zfill(2)}-{str(day).zfill(2)} at {meetup_time_str} on {platform}. Time to shine!',
                link=link,
            )
            meeting.save()

            response_data = {
                'success': True,
                'contact_name': contact.name,
                'message': meeting.message,
                'platform': platform,
                'date': date.strftime('%Y-%m-%d'),
                'time': meetup_time.strftime('%H:%M'),
                'link': link
            }
            return JsonResponse(response_data)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Contact.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Contact does not exist'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



@login_required
def create_meeting(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meeting created successfully.')
            return redirect('home')
    else:
        form = MeetingForm()
    return render(request, 'create_meeting.html', {'form': form})


@login_required
def meeting_list(request):
    meetings = Meeting.objects.all().order_by('-date')
    return render(request, 'your_template.html', {'meetings': meetings})

@login_required
def fetch_meetings(request):
    meetings = Meeting.objects.select_related('contact').all()
    results = [{
        'contact_name': meeting.contact.name,
        'message': meeting.message,
        'platform': meeting.platform,
        'date': meeting.date,
        'meetup_time': meeting.meetup_time,
        'link': meeting.link
    } for meeting in meetings]
    return JsonResponse({'results': results})

@login_required
def crm_meet_view(request):
    return render(request, 'crm_meet.html')

@login_required
def get_contacts(request):
    contacts = Contact.objects.all()
    data = list(contacts.values('id', 'name', 'phone_number'))
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required
def add_contact(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        phone_number = data.get('number')

        if name and phone_number:
            contact = Contact.objects.create(name=name, phone_number=phone_number)
            return JsonResponse({'success': True, 'id': contact.id})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid data provided.'})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

def custom_403_view(request, exception):
    return render(request, '403.html', status=403)

def check_username(request):
    username = request.GET.get('username', None)
    data = {
        'exists': User.objects.filter(username=username).exists()
    }
    return JsonResponse(data)

def check_email(request):
    email = request.GET.get('email', None)
    data = {
        'exists': User.objects.filter(email=email).exists()
    }
    return JsonResponse(data)


def schedule_meeting(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False})
    return redirect('crm_meet')

def get_upcoming_meetings(request):
    meetings = Meeting.objects.all().values('contact__name', 'platform', 'status', 'date', 'meetup_time', 'message', 'link')
    return JsonResponse(list(meetings), safe=False)

def crm_meet(request):
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    day = request.GET.get('day', '')
    status = request.GET.get('status', '')
    name = request.GET.get('name', '')
    phone_number = request.GET.get('phone_number', '')

    meetings = Meeting.objects.all()

    if year:
        meetings = meetings.filter(date__year=year)
    if month:
        meetings = meetings.filter(date__month=month)
    if day:
        meetings = meetings.filter(date__day=day)
    if status:
        meetings = meetings.filter(status__iexact=status)
    if name:
        meetings = meetings.filter(contact__name__icontains=name)
    if phone_number:
        meetings = meetings.filter(contact__phone_number__icontains=phone_number)


    context = {
        'meetings': meetings,
        'years': range(2024, 2026),  
        'months': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'days': range(1, 32),
        'statuses': ['HOT', 'WARM', 'COLD'], 
    }

    return render(request, 'crm_meet.html', context)


def crm_meet_view(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    year = int(year) if year and year.isdigit() else None
    month = int(month) if month and month.isdigit() else None
    day = int(day) if day and day.isdigit() else None
    years = range(2024, 2026)
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    days = range(1, 32)
    meetings = Meeting.objects.all()
    filters = Q()
    if year:
        filters &= Q(date__year=year)
    if month:
        filters &= Q(date__month=month)
    if day:
        filters &= Q(date__day=day)

    meetings = meetings.filter(filters)

    context = {
        'years': years,
        'months': months,
        'days': days,
        'meetings': meetings,
    }

    return render(request, 'crm_meet.html', context)

def edit_meeting(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)

    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            return redirect('crm_meet')  
    else:
        form = MeetingForm(instance=meeting)

    return render(request, 'edit_meeting.html', {'form': form})

def update_edit_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)

    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            return redirect('crm_meet')
    else:
        form = MeetingForm(instance=meeting)

    return render(request, 'edit_meeting.html', {'form': form, 'meeting': meeting})


def delete_meeting(request, meeting_id):
    if request.method == 'POST':
        meeting = get_object_or_404(Meeting, id=meeting_id)
        meeting.delete()
        return redirect('crm_meet')
    else:
        return HttpResponseNotAllowed(['POST'])
    
class MeetingDeleteView(DeleteView):
    model = Meeting
    success_url = reverse_lazy('crm_meet')
    template_name = 'confirm_delete.html'
    
def update_edit_meeting(request, id):
    meeting = get_object_or_404(Meeting, id=id)
    contact = meeting.contact 

    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            updated_meeting = form.save(commit=False)
            updated_meeting.message = meeting.message  
            updated_meeting.link = meeting.link
            updated_meeting.more = meeting.more
            updated_meeting.save()
            updated_message = f"Hooray! The meet has been set for {updated_meeting.date} at {updated_meeting.meetup_time} on {updated_meeting.platform}. Time to shine!"
            return render(request, 'edit_meeting.html', {
                'form': form,
                'meeting': updated_meeting,
                'contact': contact,
                'message': updated_message,
                'editable_fields': ['platform', 'status', 'date', 'meetup_time']
            })
        else:
            return render(request, 'edit_meeting.html', {
                'form': form,
                'meeting': meeting,
                'contact': contact,
                'message': 'There are errors in the form.',
                'editable_fields': ['platform', 'status', 'date', 'meetup_time']
            })
    else:
        form = MeetingForm(instance=meeting)
    
    return render(request, 'edit_meeting.html', {
        'form': form,
        'meeting': meeting,
        'contact': contact,
        'message': meeting.message,
        'editable_fields': ['platform', 'status', 'date', 'meetup_time']
    })
    
def reset_pass(request):
    return render(request,'reset_password.html')