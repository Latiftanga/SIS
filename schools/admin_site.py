from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model


class PlatformAdminSite(AdminSite):
    site_header = 'SmartSIS Platform Administration'
    site_title = 'SmartSIS Admin'
    index_title = 'Platform Management'
    
    def has_permission(self, request):
        """
        Only allow PlatformUsers to access the admin
        """
        from schools.models import PlatformUser
        return (
            request.user.is_active and 
            isinstance(request.user, PlatformUser) and
            request.user.is_staff
        )


# Create the platform admin site instance
platform_admin_site = PlatformAdminSite(name='platform_admin')