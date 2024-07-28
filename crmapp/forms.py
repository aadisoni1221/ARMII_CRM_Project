from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, EmailValidator
from .models import Contact, Meeting

class SignUpForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=100,
        help_text='Enter your full name'
    )
    phone_number = forms.CharField(
        max_length=20,
        help_text='Enter your phone number',
        validators=[RegexValidator(
            regex=r'^\d{10}$',
            message='Phone number must be exactly 10 digits.',
            code='invalid_phone_number'
        )]
    )
    email = forms.EmailField(
        max_length=254,
        help_text='Enter your email address',
        validators=[EmailValidator(
            message='Enter a valid email address.',
            code='invalid_email'
        )]
    )

    class Meta:
        model = User
        fields = ('username', 'full_name', 'phone_number', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        full_name = self.cleaned_data['full_name']
        names = full_name.split()
        user.first_name = names[0]
        user.last_name = ' '.join(names[1:]) if len(names) > 1 else ''
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Contact.objects.create(
                name=user.get_full_name(),
                phone_number=self.cleaned_data['phone_number']
            )
        return user

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['platform', 'status', 'date', 'meetup_time'] 
        widgets = {
            'date': forms.SelectDateWidget(years=range(2024, 2026)),
            'meetup_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }