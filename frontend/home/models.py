from django.db import models

class SiteConfiguration(models.Model):
    name = models.CharField(max_length=100, default="Site Maintenance Configuration")
    maintenance_mode = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Prevent creating more than one instance
        if not self.pk and SiteConfiguration.objects.exists():
            raise Exception("There can only be one Site Configuration.")
        return super(SiteConfiguration, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"
