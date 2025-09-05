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
from django.urls import path, include, re_path
from backend import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from pathlib import Path
from django.shortcuts import redirect

# Get BASE_DIR for serving frontend files
BASE_DIR = Path(__file__).resolve().parent.parent


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', lambda request: redirect('/frontend/index.html')),
    
    # Include API URLs
    path('api/', include('backend.api_urls')),
    
    # Serve all frontend files with a catch-all pattern
    re_path(r'^frontend/(?P<file_path>.*)$', views.serve_frontend_file, name='frontend_files'),
]

# Serve static files (for CSS, JS, images that are collected by collectstatic)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
