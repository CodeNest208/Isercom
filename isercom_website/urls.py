"""
URL configuration for isercom_website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from backend import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from pathlib import Path

# Get BASE_DIR for serving frontend files
BASE_DIR = Path(__file__).resolve().parent.parent


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Include all backend URLs (including home and static pages)
    # path('',include('backend.urls')),
    
    # Include API URLs
    path('api/', include('backend.api_urls')),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    # Serve frontend files specifically
    urlpatterns += static('frontend/', document_root=BASE_DIR / 'frontend')
