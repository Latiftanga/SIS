from django.apps import AppConfig


class SchoolsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'schools'
    verbose_name = 'School Management'

    def ready(self):
        # Customize admin site
        from django.contrib import admin
        admin.site.site_header = 'SmartSIS Platform Administration'
        admin.site.site_title = 'SmartSIS Admin'
        admin.site.index_title = 'Platform Management'