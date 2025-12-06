"""
Template tags for rendering navigation elements (sidebar and navbar).
These tags provide efficient rendering without caching complex objects.
"""
from typing import Dict, Any
from django import template
from django.http import HttpRequest

register = template.Library()


@register.inclusion_tag('core/components/sidebar.html', takes_context=True)
def render_sidebar(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render the sidebar navigation based on user role.
    """
    request: HttpRequest = context['request']
    user = request.user

    # Build context for sidebar
    return {
        'user': user,
        'request': request,
        'current_path': request.path,
        'is_admin': user.is_superuser or user.is_school_admin,
        'is_teacher': user.is_teacher,
        'is_student': user.is_student,
        'is_parent': user.is_parent,
    }


@register.inclusion_tag('core/components/navbar.html', takes_context=True)
def render_navbar(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render the navbar/header with user menu and notifications.
    """
    request: HttpRequest = context['request']
    user = request.user

    # Build context for navbar
    return {
        'user': user,
        'request': request,
        'page_title': context.get('page_title', 'Dashboard'),
        'user_avatar': user.avatar.url if user.avatar else None,
        'user_initials': user.get_short_name()[:1].upper() if user.get_short_name() else 'U',
        'user_full_name': user.get_full_name(),
        'user_type': user.get_user_type(),
        'is_admin': user.is_superuser or user.is_school_admin,
        # Pass academic session info from context processor
        'current_academic_year': context.get('current_academic_year', ''),
        'current_term': context.get('current_term', ''),
        'school_name': context.get('school_name', ''),
        'school_logo': context.get('school_logo'),
    }


@register.simple_tag
def is_active_url(request: HttpRequest, url_name: str, namespace: str = '') -> str:
    """
    Check if the current URL matches the given URL name.
    Returns 'active' class if it matches.
    """
    try:
        if namespace:
            full_name = f"{namespace}:{url_name}"
        else:
            full_name = url_name

        if request.resolver_match:
            current = f"{request.resolver_match.namespace}:{request.resolver_match.url_name}" if request.resolver_match.namespace else request.resolver_match.url_name
            return 'active' if current == full_name else ''
        return ''
    except Exception:
        return ''


@register.simple_tag
def is_active_path(request: HttpRequest, path_segment: str) -> str:
    """
    Check if the current path contains the given segment.
    Returns 'active' class if it matches.
    """
    return 'active' if path_segment in request.path else ''
