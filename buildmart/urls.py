from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/products/', include('products.urls')),
    path('api/chats/', include('chats.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/activities/', include('activities.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('accounts/', include('allauth.urls')),  # Django-allauth URLs
]

# Serve media files in development with proper headers
if settings.DEBUG:
    from django.http import HttpResponse
    from django.views.decorators.csrf import csrf_exempt
    import mimetypes
    import os
    
    @csrf_exempt
    def serve_media(request, path):
        """Serve media files with proper CORS headers and content type"""
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        
        if os.path.exists(file_path):
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Read file content
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type=content_type)
                
            # Add CORS headers
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = '*'
            
            # Ensure images display inline, not download
            if content_type and content_type.startswith('image/'):
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(path)}"'
            
            return response
        else:
            return HttpResponse('File not found', status=404)
    
    # Use custom media serving
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media, name='media'),
    ]
