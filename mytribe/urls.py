# mytribe/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Platform Configuration
router.register(r'platform-settings', views.PlatformSettingsViewSet, basename='platform-settings')
router.register(r'section-configs', views.SectionConfigViewSet, basename='section-configs')
router.register(r'splash-themes', views.SplashThemeViewSet, basename='splash-themes')

# Content
router.register(r'posts', views.PostViewSet, basename='posts')
router.register(r'events', views.EventViewSet, basename='events')
router.register(r'businesses', views.BusinessViewSet, basename='businesses')

# Engagement
router.register(r'comments', views.CommentViewSet, basename='comments')
router.register(r'featured-content', views.FeaturedContentViewSet, basename='featured-content')

# User Management
router.register(r'users', views.UserViewSet, basename='users')

# E-commerce
router.register(r'orders', views.OrderViewSet, basename='orders')
router.register(r'membership-tiers', views.MembershipTierViewSet, basename='membership-tiers')
router.register(r'user-roles', views.UserRoleViewSet, basename='user-roles')

urlpatterns = [
    # API routes
    path('api/v1/', include(router.urls)),
    
    # Authentication endpoints
    path('api/v1/auth/register/', views.register_view, name='register'),
    path('api/v1/auth/login/', views.login_view, name='login'),
    path('api/v1/auth/logout/', views.logout_view, name='logout'),
    
    # Public settings endpoint (combines multiple settings)
    path('api/v1/settings/public/', views.public_settings, name='public-settings'),
    
    # Additional user endpoints
    path('api/v1/users/me/change-password/', 
         views.UserViewSet.as_view({'post': 'change_password'}), 
         name='user-change-password'),
    path('api/v1/users/me/orders/', 
         views.UserViewSet.as_view({'get': 'my_orders'}), 
         name='user-orders'),
]

# ===============================================
# ADDITIONAL CUSTOM ENDPOINTS
# ===============================================

# These endpoints match your exact API specification

# Public Content & Platform Configuration
urlpatterns += [
    path('api/v1/settings/platform/', 
         views.PlatformSettingsViewSet.as_view({'get': 'list', 'patch': 'partial_update'}), 
         name='platform-settings'),
    path('api/v1/settings/membership-tiers/', 
         views.MembershipTierViewSet.as_view({'get': 'list'}), 
         name='membership-tiers-list'),
]

# User Authentication & Profile Management
urlpatterns += [
    path('api/v1/users/me/', 
         views.UserViewSet.as_view({'get': 'me', 'patch': 'me', 'delete': 'me'}), 
         name='user-me'),
]

# Content Interaction (Likes & Comments)
urlpatterns += [
    # These are already handled by the viewset @action decorators
    # Example: /api/v1/posts/1/toggle-like/, /api/v1/posts/1/comments/, etc.
]

# Admin endpoints (already included in router, but here for clarity)
admin_urlpatterns = [
    # Content Management CRUD - handled by viewset
    # User & Role Management - handled by viewset  
    # Membership Tiers CRUD - handled by viewset
]

# Include all admin URLs from router
urlpatterns += router.urls