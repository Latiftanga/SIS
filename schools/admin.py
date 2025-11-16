from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import *


@admin.register(School)
class SchoolAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = ('name', 'domain_url', 'created_on',)