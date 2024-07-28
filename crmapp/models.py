from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

class Contact(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.name} - {self.phone_number}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.get_full_name()} - {self.user.username}'

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'



class Meeting(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    platform = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    more = models.CharField(max_length=100)
    date = models.DateField(default=timezone.now)
    meetup_time = models.TimeField()
    message = models.TextField()
    link = models.URLField()

    def __str__(self):
        return f"{self.platform} - {self.contact.name}"

