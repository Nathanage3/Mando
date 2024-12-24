# from core.views import LogoutView
# from django.conf import settings
# from django.contrib import admin
from djoser import views as djoser_views
# from django.conf.urls.static import static 
# from django.urls import path, include
# import debug_toolbar
# from courses import views


# admin.site.site_header = 'Mando_Site Admin'
# admin.site.index_title = 'Admin'


# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', views.home, name='home'),

#     #Forgot Password Authentication
#     # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
#     # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
#     # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
#     # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
   
#     path('__debug__/', include(debug_toolbar.urls)),
#     path('notifications/', include('notifications.urls')),
#     path('course/', include('courses.urls')),  # Course-related endpoints
#     path('auth/', include('djoser.urls')),
#     path('auth/', include('djoser.urls.jwt')),
#     #path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
# ]
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import debug_toolbar
from courses import views
from core import views as core_auth

admin.site.site_header = 'Mando_Site Admin'
admin.site.index_title = 'Admin'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('__debug__/', include(debug_toolbar.urls)),
    path('notifications/', include('notifications.urls')),
    path('course/', include('courses.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/', include('djoser.urls.authtoken')),
    
    path('auth/users/set_password/', core_auth.CustomUserViewSet.as_view({'post': 'set_password'}), name='set_password'),

    path('auth/users/reset_password_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/users/reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




