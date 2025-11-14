# mytribe/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html
from .models import *

# ===============================================
# INLINES
# ===============================================

class CommentInline(GenericTabularInline):
    model = Comment
    extra = 0
    fields = ['author', 'text', 'timestamp']
    readonly_fields = ['timestamp']

class FeaturedContentInline(GenericTabularInline):
    model = FeaturedContent
    extra = 0
    fields = ['section', 'order']
    readonly_fields = ['content_object']

# ===============================================
# USER MANAGEMENT ADMINS
# ===============================================

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'permissions_summary']
    list_filter = ['is_default']
    search_fields = ['name', 'description']
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'is_default']
        }),
        ('Permissions', {
            'fields': ['permissions'],
            'description': 'Define role permissions in JSON format'
        })
    ]

    def permissions_summary(self, obj):
        return f"{len(obj.permissions)} permission sets" if obj.permissions else "No permissions"
    permissions_summary.short_description = 'Permissions'

@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'monthly_price', 'annual_price', 'is_default', 'member_count']
    list_filter = ['is_default']
    search_fields = ['name', 'description']
    fieldsets = [
        (None, {
            'fields': ['name', 'description', 'is_default']
        }),
        ('Pricing', {
            'fields': ['monthly_price', 'annual_price']
        })
    ]

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'membership_tier', 'is_staff', 'is_active']
    list_filter = ['role', 'membership_tier', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': (
                'profile_picture', 'cover_photo', 'bio', 
                'address', 'phone', 'age', 'gender', 'location'
            )
        }),
        ('Role and Membership', {
            'fields': ('role', 'membership_tier')
        })
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Information', {
            'fields': (
                'profile_picture', 'cover_photo', 'bio', 
                'address', 'phone', 'age', 'gender', 'location'
            )
        }),
        ('Role and Membership', {
            'fields': ('role', 'membership_tier')
        })
    )

# ===============================================
# PLATFORM CONFIGURATION ADMINS
# ===============================================

@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = ['app_name', 'owner_name', 'domain_name', 'primary_contact']
    fieldsets = [
        ('App Settings', {
            'fields': ['app_name', 'logo']
        }),
        ('Platform Information', {
            'fields': ['owner_name', 'domain_name', 'primary_contact']
        }),
        ('Content Configuration', {
            'fields': ['categories']
        }),
        ('Payment Settings', {
            'fields': ['currency_code', 'currency_symbol', 'payment_gateway']
        })
    ]

    def has_add_permission(self, request):
        # Only allow one instance
        return not PlatformSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(SectionConfig)
class SectionConfigAdmin(admin.ModelAdmin):
    list_display = ['section_id', 'title', 'has_splash_theme']
    list_filter = ['section_id']
    search_fields = ['title']

    def has_splash_theme(self, obj):
        return hasattr(obj, 'splash_theme')
    has_splash_theme.boolean = True
    has_splash_theme.short_description = 'Splash Theme'

@admin.register(SplashTheme)
class SplashThemeAdmin(admin.ModelAdmin):
    list_display = ['section', 'tagline', 'color', 'has_image']
    list_filter = ['section__section_id']
    search_fields = ['section__title', 'tagline']

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Has Image'

# ===============================================
# CONTENT MODEL ADMINS
# ===============================================

class BaseContentAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'updated_at', 'likes_count', 'comments_count_display', 'shares_count']
    list_per_page = 20
    
    def likes_count(self, obj):
        return obj.likes
    likes_count.short_description = 'Likes'
    
    def comments_count_display(self, obj):
        return obj.comments_count
    comments_count_display.short_description = 'Comments'
    
    def shares_count(self, obj):
        return obj.shares
    shares_count.short_description = 'Shares'

@admin.register(Post)
class PostAdmin(BaseContentAdmin):
    list_display = ['title', 'author', 'category', 'likes', 'comments_count', 'shares', 'created_at']
    list_filter = ['category', 'author', 'created_at']
    search_fields = ['title', 'description', 'author__username']
    inlines = [CommentInline]
    
    fieldsets = [
        ('Content', {
            'fields': ['title', 'description', 'image_url', 'category', 'author']
        }),
        ('Social Stats', {
            'fields': ['likes_count', 'comments_count_display', 'shares_count', 'liked_by'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    filter_horizontal = ['liked_by']

@admin.register(Event)
class EventAdmin(BaseContentAdmin):
    list_display = ['title', 'date', 'location', 'likes', 'comments_count', 'shares', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['title', 'description', 'location']
    inlines = [CommentInline]
    
    fieldsets = [
        ('Event Details', {
            'fields': ['title', 'description', 'image_url', 'date', 'location']
        }),
        ('Additional Information', {
            'fields': ['ticketing', 'features', 'gallery_images']
        }),
        ('Social Stats', {
            'fields': ['likes_count', 'comments_count_display', 'shares_count', 'liked_by'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    filter_horizontal = ['liked_by']

@admin.register(Business)
class BusinessAdmin(BaseContentAdmin):
    list_display = ['name', 'category', 'promotion', 'likes', 'comments_count', 'shares', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description', 'category', 'address']
    inlines = [CommentInline]
    
    fieldsets = [
        ('Business Information', {
            'fields': ['name', 'description', 'image_url', 'category', 'promotion']
        }),
        ('Contact Details', {
            'fields': ['address', 'website_url']
        }),
        ('Social Stats', {
            'fields': ['likes_count', 'comments_count_display', 'shares_count', 'liked_by'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    filter_horizontal = ['liked_by']

# ===============================================
# ENGAGEMENT AND RELATIONAL ADMINS
# ===============================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_object', 'parent', 'timestamp', 'text_preview']
    list_filter = ['timestamp', 'author']
    search_fields = ['author__username', 'text']
    readonly_fields = ['timestamp']
    
    fieldsets = [
        ('Comment Content', {
            'fields': ['author', 'text', 'parent']
        }),
        ('Associated Content', {
            'fields': ['content_type', 'object_id'],
            'description': 'Links this comment to the content it belongs to'
        }),
        ('Metadata', {
            'fields': ['timestamp'],
            'classes': ['collapse']
        })
    ]

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'

@admin.register(FeaturedContent)
class FeaturedContentAdmin(admin.ModelAdmin):
    list_display = ['section', 'content_object', 'order']
    list_filter = ['section__section_id']
    search_fields = ['section__title']
    list_editable = ['order']
    
    fieldsets = [
        ('Featured Content Configuration', {
            'fields': ['section', 'order']
        }),
        ('Content Association', {
            'fields': ['content_type', 'object_id'],
            'description': 'Select the content to feature in this section'
        })
    ]

# ===============================================
# E-COMMERCE ADMINS
# ===============================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['name', 'description', 'price']
    fields = ['name', 'description', 'price', 'quantity', 'item_type']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'order_date', 'total', 'item_count']
    list_filter = ['order_date', 'user']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['order_date']
    inlines = [OrderItemInline]
    
    fieldsets = [
        ('Order Information', {
            'fields': ['user', 'order_date']
        }),
        ('Financial Details', {
            'fields': ['subtotal', 'tax', 'total']
        })
    ]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'price', 'quantity', 'item_type']
    list_filter = ['item_type', 'order__order_date']
    search_fields = ['name', 'order__user__username']
    readonly_fields = ['order']
    
    fieldsets = [
        ('Item Details', {
            'fields': ['order', 'name', 'description', 'image_url', 'item_type']
        }),
        ('Pricing', {
            'fields': ['price', 'quantity']
        })
    ]

# Register the custom user admin
admin.site.register(CustomUser, CustomUserAdmin)