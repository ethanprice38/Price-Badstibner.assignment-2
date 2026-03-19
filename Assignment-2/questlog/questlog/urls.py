"""
URL configuration for the QuestLog project.

How Django URL routing works:
  1. A request comes in for a URL like /campaigns/5/
  2. Django checks each pattern in this file, top to bottom.
  3. When a pattern matches, it hands off to the linked view or include().

We use include() to break URLs into logical groups:
  - /admin/              → Django's built-in admin site
  - /accounts/login/    → Django's built-in login view
  - /accounts/logout/   → Django's built-in logout view
  - /accounts/register/ → Our custom registration view
  - everything else      → campaign_manager app URLs
"""

from django.contrib import admin
from django.urls import path, include

# Import our custom register view directly so we can attach it here.
from campaign_manager.views import register_view

urlpatterns = [
    # Django admin panel — visit /admin/ to manage data via a GUI
    path('admin/', admin.site.urls),

    # Django's built-in auth views (login, logout, password change, etc.)
    # These look for templates in registration/login.html, etc.
    path('accounts/', include('django.contrib.auth.urls')),

    # Our custom registration page (not included in django.contrib.auth.urls)
    path('accounts/register/', register_view, name='register'),

    # All other URLs are handled by the campaign_manager app
    path('', include('campaign_manager.urls')),
]
