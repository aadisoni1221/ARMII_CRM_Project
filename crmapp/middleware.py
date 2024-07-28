from django.http import HttpResponseRedirect
from django.urls import reverse

class AuthenticatedRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and self.requires_authentication(request.path):
            return HttpResponseRedirect(reverse('login'))
        response = self.get_response(request)
        return response

    def requires_authentication(self, path):
        protected_paths = [
            reverse('profile'),
            reverse('home'),
        ]
        return any(path.startswith(protected_path) for protected_path in protected_paths)


class YourMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user'):
            print("User attribute exists")
        else:
            print("User attribute is missing")
        response = self.get_response(request)
        return response


class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/') and not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        response = self.get_response(request)
        return response
