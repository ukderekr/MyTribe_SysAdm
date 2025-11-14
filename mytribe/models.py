#
# mytribe/models.py
#

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

# ===============================================
# 1. USERS AND AUTHENTICATION MODELS
# ===============================================

class UserRole(models.Model):
    """
    Defines user roles and their specific permissions.
    Corresponds to: types.ts -> UserRole
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_default = models.BooleanField(default=False, help_text="Default role for new sign-ups.")
    permissions = models.JSONField(default=dict, help_text="e.g., {'News': {'read': true, 'create': false}}")

    def __str__(self):
        return self.name

class MembershipTier(models.Model):
    """
    Defines different membership levels and pricing.
    Corresponds to: types.ts -> MembershipTier
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2)
    annual_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_default = models.BooleanField(default=False, help_text="Default tier for new users if they don't choose one.")

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    """
    Extends Django's default User model with profile information.
    Corresponds to: types.ts -> User
    """
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    cover_photo = models.ImageField(upload_to='cover_photos/', null=True, blank=True)
    bio = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, related_name='users')
    membership_tier = models.ForeignKey(MembershipTier, on_delete=models.SET_NULL, null=True, related_name='members')
    
    def __str__(self):
        return self.username


# ===============================================
# 2. PLATFORM CONFIGURATION MODELS (Singleton Pattern)
# ===============================================

class PlatformSettings(models.Model):
    """
    A singleton model to store all global platform settings.
    Corresponds to: types.ts -> PlatformSettings, AppSettings
    """
    # AppSettings
    app_name = models.CharField(max_length=100, default='Community Hub')
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)

    # PlatformSettings
    owner_name = models.CharField(max_length=100, default='Community Admin')
    domain_name = models.CharField(max_length=255, default='hub.example.com')
    primary_contact = models.EmailField(default='admin@hub.example.com')
    
    categories = models.JSONField(default=dict, help_text="Content categories, e.g., {'News': ['Community', 'Infrastructure']}")
    
    currency_code = models.CharField(max_length=3, default='GBP')
    currency_symbol = models.CharField(max_length=5, default='£')

    # Payment Gateway Choices
    GATEWAY_CHOICES = [
        ('Stripe', 'Stripe'),
        ('PayPal', 'PayPal'),
        ('SumUp', 'SumUp'),
        ('Square', 'Square'),
    ]
    payment_gateway = models.CharField(max_length=50, choices=GATEWAY_CHOICES, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Enforce a single instance of this model
        if not self.pk and PlatformSettings.objects.exists():
            raise ValidationError('There can be only one PlatformSettings instance.')
        return super(PlatformSettings, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.app_name} Settings"
    
    class Meta:
        verbose_name_plural = "Platform Settings"

class SectionConfig(models.Model):
    """
    Defines the main navigation sections of the app.
    Corresponds to: types.ts -> SectionConfig
    """
    SECTION_CHOICES = [
        ('News', 'News'),
        ('Events', 'Events'),
        ('Articles', 'Articles'),
        ('Businesses', 'Businesses'),
    ]
    section_id = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class SplashTheme(models.Model):
    """
    Stores splash screen settings for each section.
    Corresponds to: types.ts -> SplashTheme
    """
    section = models.OneToOneField(SectionConfig, on_delete=models.CASCADE, related_name='splash_theme')
    tagline = models.CharField(max_length=255)
    color = models.CharField(max_length=50, help_text="Tailwind CSS color class, e.g., 'from-blue-600'")
    image = models.ImageField(upload_to='splash_images/', null=True, blank=True)
    
    def __str__(self):
        return f"Splash Theme for {self.section.title}"


# ===============================================
# 3. CORE CONTENT MODELS
# ===============================================

class BaseContent(models.Model):
    """
    Abstract base class for all user-generated content types.
    Handles social stats and comments.
    Corresponds to: types.ts -> SocialStats
    """
    likes = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    # Generic relation to the Comment model
    comments = GenericRelation('Comment')

    # To track who liked the content
    liked_by = models.ManyToManyField(CustomUser, related_name="%(class)s_likes", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

class Post(BaseContent):
    """
    For News and Articles sections.
    Corresponds to: types.ts -> Post
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.URLField(max_length=1024, blank=True) # Or use ImageField
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='posts')
    category = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class Event(BaseContent):
    """
    For the Events section.
    Corresponds to: types.ts -> Event
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.URLField(max_length=1024, blank=True) # Or use ImageField
    date = models.CharField(max_length=100, help_text="e.g., 'August 15, 2024' or 'Every Saturday'")
    location = models.CharField(max_length=255)
    ticketing = models.JSONField(default=dict, help_text="Stores ticketing type, price, URL etc.")
    features = models.JSONField(default=list, help_text="List of features, e.g., ['Family Friendly', 'Outdoor']")
    gallery_images = models.JSONField(default=list, help_text="List of image URLs for the gallery")

    def __str__(self):
        return self.title

class Business(BaseContent):
    """
    For the Local Businesses section.
    Corresponds to: types.ts -> Business
    """
    name = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.URLField(max_length=1024, blank=True) # Or use ImageField
    category = models.CharField(max_length=100)
    promotion = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    website_url = models.URLField(max_length=1024, blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Businesses"


# ===============================================
# 4. ENGAGEMENT AND RELATIONAL MODELS
# ===============================================

class Comment(models.Model):
    """
    A generic comment model that can attach to any other model.
    Corresponds to: types.ts -> Comment
    """
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Self-referencing FK for replies
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Generic Foreign Key setup
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.timestamp.strftime("%Y-%m-%d")}'

    class Meta:
        ordering = ['-timestamp']

class FeaturedContent(models.Model):
    """
    Links a Section to a piece of content to be featured in the hero slider.
    Corresponds to: types.ts -> FeaturedContent
    """
    section = models.ForeignKey(SectionConfig, on_delete=models.CASCADE, related_name='featured_content')
    
    # Generic Foreign Key setup
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    order = models.PositiveIntegerField(default=0, help_text="Order in the slider")

    def __str__(self):
        return f"Featured in {self.section.title}: {self.content_object}"
    
    class Meta:
        ordering = ['section', 'order']
        unique_together = ('section', 'content_type', 'object_id')


# ===============================================
# 5. E-COMMERCE MODELS
# ===============================================

class Order(models.Model):
    """
    Represents a completed purchase by a user.
    Corresponds to: types.ts -> Order
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username}"
    
    class Meta:
        ordering = ['-order_date']

class OrderItem(models.Model):
    """
    Represents an item within an order.
    Corresponds to: types.ts -> CartItem
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(max_length=1024, blank=True)
    item_type = models.CharField(max_length=50, help_text="e.g., 'membership', 'event'")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    # A generic FK could link this back to the original Event/MembershipTier product,
    # but storing denormalized data (name, price) is safer for historical accuracy.
    
    def __str__(self):
        return f"{self.quantity} x {self.name} in Order #{self.order.pk}"