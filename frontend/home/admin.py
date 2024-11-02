from django.contrib import admin
from .models import SiteConfiguration

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'maintenance_mode']  # Use list_display for fields on the same model

    def has_add_permission(self, request):
        # Prevent more than one configuration from being added
        if SiteConfiguration.objects.exists():
            return False
        return True
