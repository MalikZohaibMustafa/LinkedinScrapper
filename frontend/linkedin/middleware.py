from django.shortcuts import render
from home.models import SiteConfiguration
from django.conf import settings

from django.shortcuts import render
from home.models import SiteConfiguration
from django.conf import settings

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow access to admin pages and superusers even in maintenance mode
        if request.path.startswith('/admin'):
            return self.get_response(request)

        # Fetch the first SiteConfiguration object
        config = SiteConfiguration.objects.first()

        # If maintenance mode is enabled, show the maintenance page
        if config and config.maintenance_mode:
            return render(request, 'maintenance.html')

        # Proceed with the normal request flow
        response = self.get_response(request)
        return response


from django.contrib.auth import logout
from django.conf import settings

class RestrictAdminSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the user is logged in as an admin but not visiting /admin/, log them out
        if request.user.is_authenticated and request.user.is_superuser and not request.path.startswith('/admin'):
            logout(request)  # Log the user out from public pages
        
        response = self.get_response(request)
        return response
