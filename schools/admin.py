from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.utils.html import format_html
from django.core.management import call_command
from django_tenants.utils import schema_context
from .models import School, Domain, PlatformUser
from .forms import SchoolCreationForm, SchoolChangeForm
from .admin_site import platform_admin_site  # Use custom admin site
import io


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 0
    fields = ['domain', 'is_primary']
    
    def has_add_permission(self, request, obj=None):
        return obj is not None


class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'schema_name', 'primary_domain', 'created_on']
    list_filter = ['created_on']
    search_fields = ['name', 'schema_name']
    
    add_form = SchoolCreationForm
    form = SchoolChangeForm
    inlines = [DomainInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['schema_name', 'created_on', 'access_info']
        return ['created_on']

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        else:
            kwargs['form'] = self.form
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                ('School Information', {
                    'fields': ('name', 'short_name', 'schema_name')
                }),
                ('Domain', {
                    'fields': ('domain',)
                }),
                ('Administrator Account', {
                    'fields': ('admin_email', 'admin_password', 'admin_password_confirm')
                }),
            )
        else:
            return (
                ('School Information', {
                    'fields': ('name', 'short_name', 'schema_name', 'created_on')
                }),
                ('Access', {
                    'fields': ('access_info',)
                }),
            )
        
    def get_inlines(self, request, obj):
        if obj is None:
            return []
        return self.inlines

    def primary_domain(self, obj):
        domain = obj.domains.filter(is_primary=True).first()
        if domain:
            return format_html('<a href="http://{}" target="_blank">{}</a>', domain.domain, domain.domain)
        return '-'
    primary_domain.short_description = 'Domain'

    def access_info(self, obj):
        if obj is None:
            return '-'
        
        domain = obj.domains.filter(is_primary=True).first()
        if domain:
            admin_url = f"http://{domain.domain}/admin/"
            return format_html(
                '<div style="background: #f0f9ff; padding: 15px; border-radius: 5px;">'
                '<p><strong>Admin URL:</strong> <a href="{}" target="_blank">{}</a></p>'
                '<p><strong>Schema:</strong> {}</p>'
                '</div>',
                admin_url, admin_url, obj.schema_name
            )
        return 'No domain configured'
    access_info.short_description = 'Access Info'

    def _migrate_schema(self, schema_name):
        try:
            out = io.StringIO()
            call_command('migrate_schemas', schema_name=schema_name, stdout=out, interactive=False)
            return True, out.getvalue()
        except Exception as e:
            return False, str(e)

    # Disable admin logging for this model to avoid the foreign key issue
    def log_addition(self, request, object, message):
        """Override to disable logging"""
        pass
    
    def log_change(self, request, object, message):
        """Override to disable logging"""
        pass
    
    def log_deletion(self, request, object, object_repr):
        """Override to disable logging"""
        pass

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if not change:
            try:
                super().save_model(request, obj, form, change)
                
                success, output = self._migrate_schema(obj.schema_name)
                if not success:
                    raise Exception(f'Migration failed: {output}')
                
                domain_input = form.cleaned_data['domain']
                if '.' in domain_input:
                    full_domain = domain_input
                else:
                    full_domain = f"{domain_input}.localhost"
                
                Domain.objects.create(domain=full_domain, tenant=obj, is_primary=True)
                
                admin_email = form.cleaned_data['admin_email']
                admin_password = form.cleaned_data['admin_password']
                
                with schema_context(obj.schema_name):
                    from accounts.models import User
                    User.objects.create_school_admin(email=admin_email, password=admin_password)
                
                messages.success(
                    request,
                    format_html(
                        '✅ School created!<br>'
                        '🌐 Domain: <a href="http://{}" target="_blank">{}</a><br>'
                        '👤 Admin: {}<br>'
                        '<a href="http://{}/admin/" target="_blank" style="background: #0ea5e9; color: white; '
                        'padding: 8px 16px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px;">'
                        'Access Admin Panel →</a>',
                        full_domain, full_domain, admin_email, full_domain
                    )
                )
                
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
                raise
        else:
            super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False


class PlatformUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'is_superuser', 'date_joined']
    list_filter = ['is_active', 'is_superuser']
    search_fields = ['email']
    readonly_fields = ['date_joined', 'last_login']
    
    def log_addition(self, request, object, message):
        pass
    
    def log_change(self, request, object, message):
        pass
    
    def log_deletion(self, request, object, object_repr):
        pass


class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']
    
    def log_addition(self, request, object, message):
        pass
    
    def log_change(self, request, object, message):
        pass
    
    def log_deletion(self, request, object, object_repr):
        pass


# Register with both default admin and platform admin
admin.site.register(School, SchoolAdmin)
admin.site.register(PlatformUser, PlatformUserAdmin)
admin.site.register(Domain, DomainAdmin)

# Also register with custom admin site
platform_admin_site.register(School, SchoolAdmin)
platform_admin_site.register(PlatformUser, PlatformUserAdmin)
platform_admin_site.register(Domain, DomainAdmin)