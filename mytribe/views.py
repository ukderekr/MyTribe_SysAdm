# mytribe/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from .models import *
from .serializers import *
import json

# ===============================================
# AUTHENTICATION VIEWS
# ===============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(request, username=email, password=password)
    if user is not None:
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        })
    return Response(
        {'error': 'Invalid credentials'}, 
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    logout(request)
    return Response({'message': 'Logout successful'})

# ===============================================
# PLATFORM CONFIGURATION VIEWS
# ===============================================

class PlatformSettingsViewSet(viewsets.ViewSet):
    """Handle platform settings (singleton pattern)"""
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'list':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """Get platform settings - public endpoint"""
        try:
            settings = PlatformSettings.objects.get()
            serializer = PlatformSettingsSerializer(settings)
            return Response(serializer.data)
        except PlatformSettings.DoesNotExist:
            return Response(
                {'error': 'Platform settings not configured'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def partial_update(self, request, pk=None):
        """Update platform settings - admin only"""
        try:
            settings = PlatformSettings.objects.get()
            serializer = PlatformSettingsSerializer(settings, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PlatformSettings.DoesNotExist:
            return Response(
                {'error': 'Platform settings not configured'},
                status=status.HTTP_404_NOT_FOUND
            )

class SectionConfigViewSet(viewsets.ModelViewSet):
    """Handle section configuration"""
    queryset = SectionConfig.objects.all()
    serializer_class = SectionConfigSerializer
    permission_classes = [IsAdminUser]

class SplashThemeViewSet(viewsets.ModelViewSet):
    """Handle splash screen themes"""
    queryset = SplashTheme.objects.all()
    serializer_class = SplashThemeSerializer
    permission_classes = [IsAdminUser]

# ===============================================
# CONTENT VIEWSETS
# ===============================================

class BaseContentViewSet(viewsets.ModelViewSet):
    """Base viewset for all content types with common functionality"""
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """Toggle like on content"""
        obj = self.get_object()
        user = request.user
        
        if user in obj.liked_by.all():
            obj.liked_by.remove(user)
            obj.likes = max(0, obj.likes - 1)
            liked = False
        else:
            obj.liked_by.add(user)
            obj.likes += 1
            liked = True
        
        obj.save()
        return Response({'liked': liked, 'likes': obj.likes})
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def comments(self, request, pk=None):
        """Get comments for this content"""
        obj = self.get_object()
        comments = obj.comments.filter(parent__isnull=True)  # Only top-level comments
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_comment(self, request, pk=None):
        """Add comment to content"""
        obj = self.get_object()
        serializer = CommentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                author=request.user,
                content_object=obj
            )
            obj.comments_count += 1
            obj.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostViewSet(BaseContentViewSet):
    """Handle news and articles posts"""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    def get_queryset(self):
        """Filter by type (news/article) if provided"""
        queryset = Post.objects.all()
        content_type = self.request.query_params.get('type', None)
        
        if content_type == 'news':
            # Assuming news posts have specific category or you can add a 'type' field
            queryset = queryset.filter(category__icontains='news')
        elif content_type == 'article':
            queryset = queryset.exclude(category__icontains='news')
        
        return queryset

class EventViewSet(BaseContentViewSet):
    """Handle events"""
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class BusinessViewSet(BaseContentViewSet):
    """Handle businesses"""
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer

# ===============================================
# ENGAGEMENT VIEWS
# ===============================================

class CommentViewSet(viewsets.ModelViewSet):
    """Handle comments"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reply(self, request, pk=None):
        """Add reply to comment"""
        parent_comment = self.get_object()
        serializer = CommentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                author=request.user,
                parent=parent_comment,
                content_type=parent_comment.content_type,
                object_id=parent_comment.object_id
            )
            
            # Update comments count on parent content
            content_obj = parent_comment.content_object
            content_obj.comments_count += 1
            content_obj.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FeaturedContentViewSet(viewsets.ModelViewSet):
    """Handle featured content"""
    queryset = FeaturedContent.objects.all()
    serializer_class = FeaturedContentSerializer
    permission_classes = [IsAdminUser]

# ===============================================
# USER MANAGEMENT VIEWS
# ===============================================

class UserViewSet(viewsets.ModelViewSet):
    """Handle user management"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action in ['me', 'update_me', 'change_password', 'delete_me', 'my_orders']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action in ['create', 'update', 'partial_update'] and self.request.user.is_staff:
            return UserAdminSerializer
        elif self.action in ['me', 'update_me']:
            return UserProfileSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get', 'patch', 'delete'])
    def me(self, request):
        """Handle current user's profile"""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            request.user.delete()
            return Response({'message': 'Account deleted successfully'})
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change current user's password"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get current user's orders"""
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

# ===============================================
# E-COMMERCE VIEWS
# ===============================================

class OrderViewSet(viewsets.ModelViewSet):
    """Handle orders"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own orders, admins see all"""
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create order with current user"""
        serializer.save(user=self.request.user)

class MembershipTierViewSet(viewsets.ModelViewSet):
    """Handle membership tiers"""
    queryset = MembershipTier.objects.all()
    serializer_class = MembershipTierSerializer
    
    def get_permissions(self):
        """Public read, admin write"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

class UserRoleViewSet(viewsets.ModelViewSet):
    """Handle user roles"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAdminUser]

# ===============================================
# PUBLIC VIEWS
# ===============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def public_settings(request):
    """Public endpoint for all settings needed by the app"""
    try:
        platform_settings = PlatformSettings.objects.get()
        membership_tiers = MembershipTier.objects.all()
        section_configs = SectionConfig.objects.all()
        
        data = {
            'platform': PlatformSettingsSerializer(platform_settings).data,
            'membership_tiers': MembershipTierSerializer(membership_tiers, many=True).data,
            'sections': SectionConfigSerializer(section_configs, many=True).data,
        }
        return Response(data)
    except PlatformSettings.DoesNotExist:
        return Response(
            {'error': 'Platform not configured'},
            status=status.HTTP_404_NOT_FOUND
        )