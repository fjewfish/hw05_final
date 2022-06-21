from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('posts.urls', namespace='posts')),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls', namespace='users')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about/', include('about.urls', namespace='about')),
]

handler404 = 'core.views.page_not_found'
handler500 = 'core.views.internal_server_error'

if settings.DEBUG:
    urlpatterns += path('__debug__/', include('debug_toolbar.urls')),