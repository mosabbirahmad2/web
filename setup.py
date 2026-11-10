import os
import sys

print("=" * 60)
print("🚀 Fantacy Tech: প্রজেক্ট সেটআপ ও ফাইল জেনারেশন শুরু হচ্ছে...")
print("=" * 60)

FILES = {}

# -------------------------------------------------------------
# 1. REQUIREMENTS & CONFIGURATION
# -------------------------------------------------------------
FILES["requirements.txt"] = """Django>=4.2,<6.0
Pillow>=9.5.0
python-dotenv>=1.0.0
whitenoise>=6.6.0
gunicorn>=21.2.0
dj-database-url>=2.1.0
"""

FILES[".env"] = """# Environment Configuration
DEBUG=True
SECRET_KEY=django-insecure-prod-ready-fantacy-tech-bangladesh-key-2026-xyz
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Security Settings
ADMIN_LOCKOUT_MAX_ATTEMPTS=3
ADMIN_LOCKOUT_DURATION_MINUTES=720

# Optional PostgreSQL Database (Uncomment to use Postgres instead of SQLite)
# DATABASE_URL=postgres://user:password@localhost:5432/fantacytech_db
"""

FILES["Procfile"] = """web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
"""

FILES["manage.py"] = """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""

# -------------------------------------------------------------
# 2. CORE DJANGO CONFIG
# -------------------------------------------------------------
FILES["core/__init__.py"] = ""

FILES["core/asgi.py"] = """import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_asgi_application()
"""

FILES["core/wsgi.py"] = """import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_wsgi_application()
"""

FILES["core/urls.py"] = """from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Restrict default django-admin for superuser access only
admin.site.site_header = "Fantacy Tech Superuser Gateway"
admin.site.site_title = "Fantacy Tech Admin"
admin.site.index_title = "Core Infrastructure Administration"

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.BASE_DIR / 'static')
"""

FILES["core/settings.py"] = """import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-fallback-key-for-local-testing-only'
    else:
        raise RuntimeError("CRITICAL: SECRET_KEY environment variable is missing in production mode (DEBUG=False).")

allowed_hosts_raw = os.getenv('ALLOWED_HOSTS', '')
if not allowed_hosts_raw and not DEBUG:
    raise RuntimeError("CRITICAL: ALLOWED_HOSTS must be set in production.")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(',') if h.strip()] if allowed_hosts_raw else ['*'] if DEBUG else []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'products.apps.ProductsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'products.middleware.AnalyticsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'products.context_processors.site_settings_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

import dj_database_url
database_url = os.getenv('DATABASE_URL')
if database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'fantacytech-local-cache',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/mosabbiradmin/login/'
LOGIN_REDIRECT_URL = '/mosabbiradmin/'
LOGOUT_REDIRECT_URL = '/mosabbiradmin/login/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
"""

# -------------------------------------------------------------
# 3. PRODUCTS APP
# -------------------------------------------------------------
FILES["products/__init__.py"] = ""

FILES["products/apps.py"] = """from django.apps import AppConfig

class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
"""

FILES["products/admin.py"] = """from django.contrib import admin
from .models import Category, Product, ProductImage, ProductReview, Order, OrderItem, PromoCode, SiteSetting

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_price', 'stock', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')

admin.site.register(ProductImage)
admin.site.register(ProductReview)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(PromoCode)
admin.site.register(SiteSetting)
"""

FILES["products/context_processors.py"] = """from .models import SiteSetting

def site_settings_processor(request):
    return {
        'site_setting': SiteSetting.get_settings()
    }
"""

FILES["products/middleware.py"] = """from .models import AnalyticsEvent

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not path.startswith('/static/') and not path.startswith('/media/') and not path.startswith('/django-admin/'):
            ua = request.META.get('HTTP_USER_AGENT', '')
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip:
                ip = ip.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

            ua_lower = ua.lower()
            device = 'Mobile' if any(w in ua_lower for w in ['mobile', 'android', 'iphone']) else 'Desktop'
            if 'chrome' in ua_lower and 'edg' not in ua_lower:
                browser = 'Chrome'
            elif 'firefox' in ua_lower:
                browser = 'Firefox'
            elif 'safari' in ua_lower and 'chrome' not in ua_lower:
                browser = 'Safari'
            elif 'edg' in ua_lower:
                browser = 'Edge'
            else:
                browser = 'Other'

            try:
                AnalyticsEvent.objects.create(
                    ip_address=ip,
                    user_agent=ua[:200],
                    device_type=device,
                    browser=browser,
                    path=path[:250],
                    event_type='visit',
                    referrer=request.META.get('HTTP_REFERER', '')[:250]
                )
            except Exception:
                pass

        return self.get_response(request)
"""

FILES["products/models.py"] = """import os
import uuid
from io import BytesIO
from PIL import Image

from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models import Avg

def optimize_image(image_field, max_size=(1000, 1000), quality=85):
    if not image_field:
        return
    try:
        img = Image.open(image_field)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, format='WEBP', quality=quality, optimize=True)
        output.seek(0)
        orig_name = os.path.splitext(image_field.name)[0]
        image_field.save(f"{orig_name}.webp", ContentFile(output.read()), save=False)
    except Exception:
        pass


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=100, default="Fantacy Tech")
    contact_phone = models.CharField(max_length=30, default="01999999999")
    whatsapp_number = models.CharField(max_length=30, default="01999999999")
    whatsapp_username = models.CharField(max_length=100, default="fantacytech", blank=True)
    contact_email = models.EmailField(default="support@fantacytech.com")
    office_address = models.TextField(default="Dhaka, Bangladesh")
    announcement_notice = models.CharField(
        max_length=300, 
        default="Welcome to Fantacy Tech! Premium Phone Covers, Key Rings & Accessories with Fast Home Delivery!"
    )
    delivery_fee_dhaka = models.DecimalField(max_digits=6, decimal_places=2, default=70.00)
    delivery_fee_outside = models.DecimalField(max_digits=6, decimal_places=2, default=130.00)
    theme_color = models.CharField(max_length=30, default="#5C3214")
    theme_mode = models.CharField(max_length=10, default="light", choices=(('light', 'Light'), ('dark', 'Dark')))
    enable_buy_now = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.site_name} Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        setting, _ = cls.objects.get_or_create(pk=1)
        return setting


class AdminLoginAttempt(models.Model):
    ip_address = models.GenericIPAddressField()
    username = models.CharField(max_length=150, default="admin")
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('ip_address', 'username')

    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def __str__(self):
        return f"{self.username} @ {self.ip_address} - Failed: {self.failed_attempts}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    short_description = models.TextField(blank=True, null=True)
    banner = models.ImageField(upload_to='categories/banners/', blank=True, null=True)
    image = models.ImageField(upload_to='categories/images/', blank=True, null=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "cat"
            slug = base_slug
            c = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{c}"
                c += 1
            self.slug = slug
        if self.image:
            optimize_image(self.image, max_size=(500, 500))
        if self.banner:
            optimize_image(self.banner, max_size=(1400, 400))
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Regular Price (BDT)")
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Offer Sale Price")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=50)
    badge_tag = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Hot Product, Top Selling")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.discount_price and self.discount_price > self.price:
            raise ValidationError({'discount_price': 'Discount price cannot exceed regular price.'})

    def save(self, *args, **kwargs):
        if self.discount_price and self.discount_price > self.price:
            self.discount_price = self.price
        if not self.slug:
            base_slug = slugify(self.name) or "prod"
            slug = base_slug
            c = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{c}"
                c += 1
            self.slug = slug
        if self.image:
            optimize_image(self.image, max_size=(900, 900))
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        if self.discount_price and self.discount_price > 0:
            return min(self.price, self.discount_price)
        return self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.discount_price < self.price:
            diff = self.price - self.discount_price
            return int((diff / self.price) * 100)
        return 0

    @property
    def avg_rating(self):
        avg = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 5.0

    @property
    def reviews_count(self):
        return self.reviews.filter(is_approved=True).count()

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image:
            optimize_image(self.image, max_size=(900, 900))
        super().save(*args, **kwargs)


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer_name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ShowcaseSection(models.Model):
    STYLE_CHOICES = (
        ('light', 'White / Light Minimal'),
        ('brown', 'Warm Coffee Brown (Dazzle Style)'),
        ('dark', 'Dark Charcoal Black'),
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    background_style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='light')
    has_countdown = models.BooleanField(default=False)
    end_time = models.DateTimeField(null=True, blank=True, help_text="Countdown expiration datetime")
    products = models.ManyToManyField(Product, blank=True, related_name='showcases')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def is_expired(self):
        if self.has_countdown and self.end_time and self.end_time <= timezone.now():
            return True
        return False

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "section"
            slug = base_slug
            c = 1
            while ShowcaseSection.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{c}"
                c += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PromoCode(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.PositiveIntegerField(default=10, help_text="Amount or Percentage")
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self, subtotal=0):
        if not self.is_active:
            return False, "This promo code is currently disabled."
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False, "This promo code has expired."
        if self.min_purchase and subtotal < self.min_purchase:
            return False, f"Minimum purchase amount of ৳{self.min_purchase} is required to use this code."
        return True, "Valid"

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / 100
            if self.max_discount and discount > self.max_discount:
                discount = self.max_discount
        else:
            discount = self.discount_value
        return min(discount, subtotal)

    def __str__(self):
        return self.code


class Order(models.Model):
    STATUS_CHOICES = (
        ('Placed', 'Placed'),
        ('On Hold', 'On Hold'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
        ('PaymentOnProcess', 'PaymentOnProcess'),
        ('Payment Failed', 'Payment Failed'),
    )
    order_id = models.CharField(max_length=32, unique=True, editable=False)
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=25)
    customer_email = models.EmailField(blank=True, null=True)
    delivery_zone = models.CharField(max_length=50, default="Inside Dhaka")
    district = models.CharField(max_length=80, default="Dhaka")
    thana = models.CharField(max_length=80, blank=True, null=True)
    shipping_address = models.TextField()
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=70.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='Placed')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"FT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product_name or (self.product.name if self.product else 'Item')}"


class UniqueVisitorLog(models.Model):
    ip_address = models.GenericIPAddressField()
    session_key = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ip_address', 'date')
        ordering = ['-created_at']


class AnalyticsEvent(models.Model):
    EVENT_TYPES = (
        ('visit', 'Unique Visit'),
        ('product_view', 'Product View'),
        ('add_to_cart', 'Add to Cart'),
        ('checkout_start', 'Checkout Started'),
        ('order_completed', 'Order Completed'),
        ('search', 'Search Query'),
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default='')
    device_type = models.CharField(max_length=30, blank=True, default='Desktop')
    browser = models.CharField(max_length=40, blank=True, default='Chrome')
    referrer = models.CharField(max_length=255, blank=True, default='')
    path = models.CharField(max_length=255)
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES, default='visit')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']


class SearchQuery(models.Model):
    query = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
"""

FILES["products/migrations/__init__.py"] = ""

# -------------------------------------------------------------
# 4. VIEWS AND URLS
# -------------------------------------------------------------
FILES["products/urls.py"] = """from django.urls import path
from . import views

urlpatterns = [
    # Storefront
    path('', views.home_view, name='home'),
    path('category/<slug:slug>/', views.shop_category_view, name='shop_category'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('product/<int:pk>/review/', views.add_product_review, name='add_product_review'),
    
    # Storefront APIs
    path('api/apply-promo/', views.apply_promo_api, name='apply_promo_api'),
    path('api/checkout/', views.place_order_api, name='place_order_api'),
    path('api/log-event/', views.log_event_api, name='log_event_api'),

    # Admin Login / Logout
    path('mosabbiradmin/login/', views.admin_login_view, name='admin_login'),
    path('mosabbiradmin/logout/', views.admin_logout_view, name='admin_logout'),

    # Admin Dashboard & Orders
    path('mosabbiradmin/', views.merchant_dashboard, name='merchant_dashboard'),
    path('mosabbiradmin/orders/', views.merchant_orders, name='merchant_orders'),
    path('mosabbiradmin/orders/export/', views.export_orders_csv, name='export_orders_csv'),
    path('mosabbiradmin/orders/bulk/', views.bulk_order_action, name='bulk_order_action'),
    path('mosabbiradmin/orders/<int:pk>/update/', views.update_order_status, name='update_order_status'),

    # Products CRUD
    path('mosabbiradmin/products/', views.merchant_products, name='merchant_products'),
    path('mosabbiradmin/products/add/', views.add_product, name='add_product'),
    path('mosabbiradmin/products/bulk/', views.bulk_product_action, name='bulk_product_action'),
    path('mosabbiradmin/products/<int:pk>/edit/', views.merchant_edit_product, name='merchant_edit_product'),
    path('mosabbiradmin/products/<int:pk>/delete/', views.merchant_delete_product, name='merchant_delete_product'),

    # Categories
    path('mosabbiradmin/categories/', views.merchant_categories, name='merchant_categories'),
    path('mosabbiradmin/categories/<int:pk>/', views.merchant_category_detail, name='merchant_category_detail'),
    path('mosabbiradmin/categories/<int:pk>/toggle/', views.merchant_toggle_category, name='merchant_toggle_category'),
    path('mosabbiradmin/categories/<int:pk>/delete/', views.merchant_delete_category, name='merchant_delete_category'),

    # Customers
    path('mosabbiradmin/customers/', views.merchant_customers, name='merchant_customers'),

    # Showcase Sections
    path('mosabbiradmin/sections/', views.merchant_sections, name='merchant_sections'),
    path('mosabbiradmin/sections/<int:pk>/edit/', views.merchant_edit_section, name='merchant_edit_section'),
    path('mosabbiradmin/sections/<int:pk>/toggle/', views.merchant_toggle_section, name='merchant_toggle_section'),
    path('mosabbiradmin/sections/<int:pk>/delete/', views.merchant_delete_section, name='merchant_delete_section'),

    # Settings & Theme Customization
    path('mosabbiradmin/settings/', views.merchant_settings, name='merchant_settings'),
    path('mosabbiradmin/customize-theme/', views.merchant_customize_theme, name='merchant_customize_theme'),

    # Analytics & Reports
    path('mosabbiradmin/analytics/', views.merchant_analytics, name='merchant_analytics'),

    # Promo Codes
    path('mosabbiradmin/promos/', views.merchant_promos, name='merchant_promos'),
    path('mosabbiradmin/promos/<int:pk>/toggle/', views.toggle_promo, name='toggle_promo'),
    path('mosabbiradmin/promos/<int:pk>/delete/', views.delete_promo, name='delete_promo'),
]
"""

FILES["products/views.py"] = """import csv
import json
import os
from decimal import Decimal
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum, Q, Avg
from django.db.models.functions import TruncDate, TruncHour
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Category, Product, ProductImage, ProductReview, Order, OrderItem,
    AnalyticsEvent, PromoCode, ShowcaseSection, SiteSetting,
    AdminLoginAttempt, SearchQuery, UniqueVisitorLog
)

def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

# --- AUTHENTICATION (GRANULAR IP + USERNAME LOCKOUT) ---
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('merchant_dashboard')

    ip = get_client_ip(request)
    max_attempts = int(os.getenv('ADMIN_LOCKOUT_MAX_ATTEMPTS', 3))
    duration_mins = int(os.getenv('ADMIN_LOCKOUT_DURATION_MINUTES', 720))

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()

        attempt, _ = AdminLoginAttempt.objects.get_or_create(ip_address=ip, username=u)

        if attempt.is_locked():
            remaining = attempt.locked_until - timezone.now()
            hours = int(remaining.total_seconds() // 3600)
            mins = int((remaining.total_seconds() % 3600) // 60)
            messages.error(request, f"Security Alert: Your access is locked out for {hours}h {mins}m.")
            return render(request, 'admin_custom/login.html', {'locked': True})

        user = authenticate(request, username=u, password=p)
        if user is not None and user.is_staff:
            attempt.failed_attempts = 0
            attempt.locked_until = None
            attempt.save()
            login(request, user)
            return redirect(request.GET.get('next') or 'merchant_dashboard')
        else:
            attempt.failed_attempts += 1
            if attempt.failed_attempts >= max_attempts:
                attempt.locked_until = timezone.now() + timedelta(minutes=duration_mins)
                attempt.save()
                messages.error(request, f"Security Alert: {max_attempts} failed attempts. Account locked for {duration_mins // 60} hours.")
            else:
                attempt.save()
                messages.error(request, f"Invalid credentials! Remaining attempts: {max_attempts - attempt.failed_attempts}")

    return render(request, 'admin_custom/login.html')

def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')

# --- STOREFRONT VIEWS ---
def home_view(request):
    ip = get_client_ip(request)
    today = timezone.now().date()
    UniqueVisitorLog.objects.get_or_create(ip_address=ip, date=today)

    categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('subcategories')
    showcase_sections = ShowcaseSection.objects.filter(is_active=True).prefetch_related(
        'products__category'
    )
    
    # Exclude expired showcase sections
    valid_sections = [s for s in showcase_sections if not s.is_expired()]

    # Homepage all products with pagination
    products_list = Product.objects.filter(is_active=True).select_related('category').order_by('-created_at')
    paginator = Paginator(products_list, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'index.html', {
        'categories': categories,
        'showcase_sections': valid_sections,
        'products': page_obj,
    })

def shop_category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    sub_ids = category.subcategories.values_list('id', flat=True)
    products = Product.objects.filter(
        Q(category=category) | Q(category__id__in=sub_ids),
        is_active=True
    ).distinct().select_related('category')

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'shop/category_products.html', {
        'category': category,
        'products': page_obj
    })

def product_detail_view(request, pk):
    product = get_object_or_404(Product.objects.select_related('category').prefetch_related('images', 'reviews'), pk=pk)
    product.views_count += 1
    product.save(update_fields=['views_count'])

    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:5]

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': product.reviews.filter(is_approved=True)
    })

@require_POST
def add_product_review(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = request.POST.get('name', 'Anonymous').strip()
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '').strip()

    if comment:
        ProductReview.objects.create(
            product=product, customer_name=name, rating=rating, comment=comment
        )
        messages.success(request, 'Thank you! Your review has been added.')
    return redirect('product_detail', pk=pk)

# --- SECURE APIS (CSRF PROTECTED & VALIDATED) ---
@require_POST
def apply_promo_api(request):
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
        subtotal = Decimal(str(data.get('subtotal', 0)))

        promo = PromoCode.objects.filter(code=code).first()
        if not promo:
            return JsonResponse({'status': 'error', 'message': 'Invalid promo code!'}, status=400)

        is_valid, msg = promo.is_valid(subtotal=subtotal)
        if not is_valid:
            return JsonResponse({'status': 'error', 'message': msg}, status=400)

        discount = promo.calculate_discount(subtotal=subtotal)
        return JsonResponse({
            'status': 'success',
            'code': promo.code,
            'discount': float(discount),
            'new_total': float(max(Decimal('0.00'), subtotal - discount))
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
def log_event_api(request):
    try:
        data = json.loads(request.body)
        event_type = data.get('event_type')
        product_id = data.get('product_id')
        query = data.get('query')

        if query:
            SearchQuery.objects.create(query=query.strip(), ip_address=get_client_ip(request))

        product = Product.objects.filter(id=product_id).first() if product_id else None
        AnalyticsEvent.objects.create(
            ip_address=get_client_ip(request),
            path=request.path,
            event_type=event_type,
            product=product
        )
        return JsonResponse({'status': 'ok'})
    except Exception:
        return JsonResponse({'status': 'ok'})

@require_POST
def place_order_api(request):
    # Cooldown rate-limit protection: 1 order per 5 seconds per IP
    ip = get_client_ip(request)
    cache_key = f"order_cooldown_{ip}"
    if cache.get(cache_key):
        return JsonResponse({'status': 'error', 'message': 'Please wait a moment before placing another order.'}, status=429)

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        district = data.get('district', 'Dhaka').strip()
        thana = data.get('thana', '').strip()
        address = data.get('address', '').strip()
        promo_code_str = data.get('promo_code', '').strip().upper()
        items = data.get('items', [])

        if not name or not phone or not address or not items:
            return JsonResponse({'status': 'error', 'message': 'Please fill out all delivery fields!'}, status=400)

        setting = SiteSetting.get_settings()
        is_dhaka = (district.lower() == 'dhaka')
        delivery_fee = setting.delivery_fee_dhaka if is_dhaka else setting.delivery_fee_outside

        # ATOMIC TRANSACTION WITH ROW-LEVEL LOCKING & SERVER-SIDE PRICE/STOCK RE-VALIDATION
        with transaction.atomic():
            subtotal = Decimal('0.00')
            validated_items = []

            for item in items:
                prod_id = item.get('id')
                qty = int(item.get('qty', 1))
                if qty <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Invalid product quantity.'}, status=400)

                # Row-level lock to prevent concurrent overselling race conditions
                prod = Product.objects.select_for_update().filter(id=prod_id, is_active=True).first()
                if not prod:
                    return JsonResponse({'status': 'error', 'message': f'Product ID {prod_id} is no longer available.'}, status=400)

                if prod.stock < qty:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Insufficient stock for "{prod.name}". Only {prod.stock} unit(s) left.'
                    }, status=400)

                # Re-validate price directly from database
                item_price = prod.effective_price
                subtotal += (Decimal(str(item_price)) * qty)
                validated_items.append((prod, qty, item_price))

            # Validate Promo Code if provided
            discount_amount = Decimal('0.00')
            applied_promo = None
            if promo_code_str:
                applied_promo = PromoCode.objects.filter(code=promo_code_str).first()
                if applied_promo:
                    valid, _ = applied_promo.is_valid(subtotal=subtotal)
                    if valid:
                        discount_amount = Decimal(str(applied_promo.calculate_discount(subtotal=subtotal)))

            total_amount = max(Decimal('0.00'), subtotal - discount_amount) + Decimal(str(delivery_fee))

            # Create Order
            order = Order.objects.create(
                customer_name=name,
                customer_phone=phone,
                district=district,
                thana=thana,
                shipping_address=address,
                delivery_zone="Inside Dhaka" if is_dhaka else "Outside Dhaka",
                delivery_fee=delivery_fee,
                discount_amount=discount_amount,
                promo_code=applied_promo,
                status='Placed',
                total_amount=total_amount
            )

            # Create Order Items and Deduct Stock safely
            for prod, qty, price in validated_items:
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    product_name=prod.name,
                    quantity=qty,
                    price=price
                )
                prod.stock -= qty
                prod.save(update_fields=['stock'])

            # Log Analytics Event
            AnalyticsEvent.objects.create(
                ip_address=ip,
                path='/checkout/success',
                event_type='order_completed'
            )

            # Set cooldown for IP
            cache.set(cache_key, True, timeout=5)

            return JsonResponse({
                'status': 'success',
                'order_id': order.order_id,
                'total': str(order.total_amount)
            })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# --- MERCHANT ADMIN VIEWS ---
@login_required(login_url='admin_login')
def merchant_dashboard(request):
    total_sales = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_visitors = UniqueVisitorLog.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:8]

    return render(request, 'merchant/dashboard.html', {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_visitors': total_visitors,
        'recent_orders': recent_orders,
        'active_menu': 'dashboard',
    })

@login_required(login_url='admin_login')
def merchant_orders(request):
    status_filter = request.GET.get('status', 'all').strip()
    search_query = request.GET.get('q', '').strip()
    orders = Order.objects.all().order_by('-created_at')

    if status_filter and status_filter.lower() != 'all':
        orders = orders.filter(status__iexact=status_filter)
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) | 
            Q(customer_phone__icontains=search_query) | 
            Q(district__icontains=search_query)
        )

    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'merchant/orders.html', {
        'orders': page_obj,
        'active_menu': 'orders',
        'status_filter': status_filter,
        'search_query': search_query,
    })

@login_required(login_url='admin_login')
@require_POST
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status = request.POST.get('status')
    if status in dict(Order.STATUS_CHOICES):
        order.status = status
        order.save(update_fields=['status'])
        messages.success(request, f'Order {order.order_id} updated to {status}.')
    return redirect('merchant_orders')

@login_required(login_url='admin_login')
@require_POST
def bulk_order_action(request):
    order_ids = request.POST.getlist('selected_orders')
    action = request.POST.get('bulk_action')

    if order_ids and action:
        if action in dict(Order.STATUS_CHOICES):
            Order.objects.filter(id__in=order_ids).update(status=action)
            messages.success(request, f'Updated {len(order_ids)} orders to {action}.')
        elif action == 'delete':
            Order.objects.filter(id__in=order_ids).delete()
            messages.success(request, f'Deleted {len(order_ids)} selected orders.')
    return redirect('merchant_orders')

@login_required(login_url='admin_login')
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fantacy_orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Phone', 'District', 'Thana', 'Address', 'Fee', 'Discount', 'Total', 'Status', 'Date'])
    for o in Order.objects.all().order_by('-created_at'):
        writer.writerow([o.order_id, o.customer_name, o.customer_phone, o.district, o.thana or '', o.shipping_address, o.delivery_fee, o.discount_amount, o.total_amount, o.status, o.created_at.strftime('%Y-%m-%d %H:%M')])
    return response

@login_required(login_url='admin_login')
def merchant_customers(request):
    search = request.GET.get('q', '').strip()
    customers_qs = Order.objects.values('customer_name', 'customer_phone').annotate(
        orders_count=Count('id'),
        total_spent=Sum('total_amount')
    ).order_by('-orders_count')

    if search:
        customers_qs = customers_qs.filter(Q(customer_name__icontains=search) | Q(customer_phone__icontains=search))

    paginator = Paginator(customers_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'merchant/customers.html', {
        'customers': page_obj,
        'active_menu': 'customers',
        'search_query': search,
    })

@login_required(login_url='admin_login')
def merchant_products(request):
    search = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category', '').strip()
    products_qs = Product.objects.all().select_related('category').order_by('-created_at')

    if search:
        products_qs = products_qs.filter(name__icontains=search)
    if cat_id:
        products_qs = products_qs.filter(category_id=cat_id)

    paginator = Paginator(products_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    categories = Category.objects.all()

    return render(request, 'merchant/products.html', {
        'products': page_obj,
        'categories': categories,
        'active_menu': 'products',
        'search_query': search,
        'selected_category': cat_id,
    })

@login_required(login_url='admin_login')
@require_POST
def add_product(request):
    name = request.POST.get('name', '').strip()
    category_id = request.POST.get('category')
    description = request.POST.get('description', '').strip()
    price = request.POST.get('price')
    discount_price = request.POST.get('discount_price')
    stock = request.POST.get('stock', 50)
    badge_tag = request.POST.get('badge_tag', '').strip()
    is_featured = bool(request.POST.get('is_featured'))
    main_image = request.FILES.get('main_image')
    gallery_images = request.FILES.getlist('gallery_images')

    if name and category_id and price:
        category = get_object_or_404(Category, pk=category_id)
        d_price = Decimal(str(discount_price)) if discount_price else None
        r_price = Decimal(str(price))
        if d_price and d_price > r_price:
            d_price = r_price

        prod = Product.objects.create(
            name=name, category=category, description=description,
            price=r_price, discount_price=d_price, stock=stock,
            badge_tag=badge_tag, is_featured=is_featured, image=main_image
        )
        for g_img in gallery_images:
            ProductImage.objects.create(product=prod, image=g_img)

        messages.success(request, f'Product "{name}" added successfully!')
    return redirect('merchant_products')

@login_required(login_url='admin_login')
def merchant_edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        cat_id = request.POST.get('category')
        if cat_id:
            product.category = get_object_or_404(Category, pk=cat_id)
        product.description = request.POST.get('description', '').strip()
        product.price = Decimal(str(request.POST.get('price', product.price)))
        d_price = request.POST.get('discount_price')
        product.discount_price = Decimal(str(d_price)) if d_price else None
        product.stock = int(request.POST.get('stock', product.stock))
        product.badge_tag = request.POST.get('badge_tag', '').strip()
        product.is_featured = bool(request.POST.get('is_featured'))

        if 'main_image' in request.FILES:
            product.image = request.FILES['main_image']

        product.save()

        for g_img in request.FILES.getlist('gallery_images'):
            ProductImage.objects.create(product=product, image=g_img)

        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('merchant_products')

    return render(request, 'merchant/products.html', {
        'products': Product.objects.all().order_by('-created_at')[:15],
        'categories': categories,
        'edit_product': product,
        'active_menu': 'products',
    })

@login_required(login_url='admin_login')
@require_POST
def merchant_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f'Product "{name}" deleted successfully!')
    return redirect('merchant_products')

@login_required(login_url='admin_login')
@require_POST
def bulk_product_action(request):
    product_ids = request.POST.getlist('selected_products')
    action = request.POST.get('bulk_action')

    if product_ids and action:
        if action == 'activate':
            Product.objects.filter(id__in=product_ids).update(is_active=True)
            messages.success(request, f'Activated {len(product_ids)} products.')
        elif action == 'deactivate':
            Product.objects.filter(id__in=product_ids).update(is_active=False)
            messages.success(request, f'Deactivated {len(product_ids)} products.')
        elif action == 'delete':
            Product.objects.filter(id__in=product_ids).delete()
            messages.success(request, f'Deleted {len(product_ids)} products.')
    return redirect('merchant_products')

# Categories
@login_required(login_url='admin_login')
def merchant_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        short_description = request.POST.get('short_description', '').strip()
        banner = request.FILES.get('banner')
        image = request.FILES.get('image')
        if name:
            Category.objects.create(name=name, short_description=short_description, banner=banner, image=image)
            messages.success(request, f'Category "{name}" created successfully!')
        return redirect('merchant_categories')

    search = request.GET.get('q', '')
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
    if search:
        categories = categories.filter(name__icontains=search)

    return render(request, 'merchant/categories.html', {
        'categories': categories,
        'search_query': search,
        'active_menu': 'categories',
    })

@login_required(login_url='admin_login')
def merchant_category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_category':
            category.name = request.POST.get('name', category.name).strip()
            category.short_description = request.POST.get('short_description', category.short_description).strip()
            if 'banner' in request.FILES: category.banner = request.FILES['banner']
            if 'image' in request.FILES: category.image = request.FILES['image']
            category.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('merchant_category_detail', pk=category.pk)

        elif action == 'create_subcategory':
            sub_name = request.POST.get('name', '').strip()
            sub_desc = request.POST.get('short_description', '').strip()
            if sub_name:
                Category.objects.create(
                    name=sub_name, short_description=sub_desc,
                    banner=request.FILES.get('banner'), image=request.FILES.get('image'),
                    parent=category
                )
                messages.success(request, f'Sub-category "{sub_name}" created successfully!')
            return redirect('merchant_category_detail', pk=category.pk)

    return render(request, 'merchant/category_detail.html', {
        'category': category,
        'subcategories': category.subcategories.all(),
        'active_menu': 'categories',
    })

@login_required(login_url='admin_login')
@require_POST
def merchant_toggle_category(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    cat.is_active = not cat.is_active
    cat.save(update_fields=['is_active'])
    return redirect(request.META.get('HTTP_REFERER', 'merchant_categories'))

@login_required(login_url='admin_login')
@require_POST
def merchant_delete_category(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    parent_id = cat.parent.pk if cat.parent else None
    cat.delete()
    messages.success(request, 'Category deleted successfully!')
    return redirect('merchant_category_detail', pk=parent_id) if parent_id else redirect('merchant_categories')

# Showcase Sections
@login_required(login_url='admin_login')
def merchant_sections(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        bg_style = request.POST.get('background_style', 'light')
        has_countdown = bool(request.POST.get('has_countdown'))
        end_time = request.POST.get('end_time') or None
        product_ids = request.POST.getlist('products')

        if title:
            sec = ShowcaseSection.objects.create(
                title=title, background_style=bg_style, 
                has_countdown=has_countdown, end_time=end_time
            )
            if product_ids: sec.products.set(product_ids)
            messages.success(request, f'Section "{title}" added to Homepage!')
        return redirect('merchant_sections')

    sections = ShowcaseSection.objects.all().prefetch_related('products')
    all_products = Product.objects.filter(is_active=True)
    return render(request, 'merchant/sections.html', {
        'sections': sections,
        'all_products': all_products,
        'active_menu': 'sections',
    })

@login_required(login_url='admin_login')
@require_POST
def merchant_edit_section(request, pk):
    sec = get_object_or_404(ShowcaseSection, pk=pk)
    sec.title = request.POST.get('title', sec.title).strip()
    sec.background_style = request.POST.get('background_style', sec.background_style)
    sec.has_countdown = bool(request.POST.get('has_countdown'))
    sec.end_time = request.POST.get('end_time') or None
    product_ids = request.POST.getlist('products')
    sec.products.set(product_ids)
    sec.save()
    messages.success(request, f'Section "{sec.title}" updated!')
    return redirect('merchant_sections')

@login_required(login_url='admin_login')
@require_POST
def merchant_toggle_section(request, pk):
    sec = get_object_or_404(ShowcaseSection, pk=pk)
    sec.is_active = not sec.is_active
    sec.save(update_fields=['is_active'])
    return redirect('merchant_sections')

@login_required(login_url='admin_login')
@require_POST
def merchant_delete_section(request, pk):
    sec = get_object_or_404(ShowcaseSection, pk=pk)
    sec.delete()
    messages.success(request, 'Section deleted successfully!')
    return redirect('merchant_sections')

# Settings & Customizer
@login_required(login_url='admin_login')
def merchant_settings(request):
    setting = SiteSetting.get_settings()
    if request.method == 'POST':
        setting.site_name = request.POST.get('site_name', setting.site_name).strip()
        setting.contact_phone = request.POST.get('contact_phone', setting.contact_phone).strip()
        setting.whatsapp_number = request.POST.get('whatsapp_number', setting.whatsapp_number).strip()
        setting.whatsapp_username = request.POST.get('whatsapp_username', setting.whatsapp_username).strip()
        setting.contact_email = request.POST.get('contact_email', setting.contact_email).strip()
        setting.office_address = request.POST.get('office_address', setting.office_address).strip()
        setting.announcement_notice = request.POST.get('announcement_notice', setting.announcement_notice).strip()
        setting.delivery_fee_dhaka = Decimal(request.POST.get('delivery_fee_dhaka', setting.delivery_fee_dhaka))
        setting.delivery_fee_outside = Decimal(request.POST.get('delivery_fee_outside', setting.delivery_fee_outside))
        setting.save()
        messages.success(request, 'Site settings updated successfully!')
        return redirect('merchant_settings')

    return render(request, 'merchant/settings.html', {'setting': setting, 'active_menu': 'settings'})

@login_required(login_url='admin_login')
def merchant_customize_theme(request):
    setting = SiteSetting.get_settings()
    if request.method == 'POST':
        setting.theme_color = request.POST.get('theme_color', setting.theme_color)
        setting.theme_mode = request.POST.get('theme_mode', setting.theme_mode)
        setting.enable_buy_now = (request.POST.get('enable_buy_now') == 'yes')
        setting.save()
        messages.success(request, 'Theme customization saved successfully!')
        return redirect('merchant_customize_theme')

    return render(request, 'merchant/customize_theme.html', {'setting': setting, 'active_menu': 'themes'})

# Analytics Engine with Visual Chart.js Data
@login_required(login_url='admin_login')
def merchant_analytics(request):
    period = request.GET.get('period', '7d').lower()
    now = timezone.now()

    if period == '12h':
        start_time = now - timedelta(hours=12)
        trunc_fn = TruncHour
        date_format = '%I %p'
    elif period == '24h':
        start_time = now - timedelta(hours=24)
        trunc_fn = TruncHour
        date_format = '%I %p'
    elif period == '48h':
        start_time = now - timedelta(hours=48)
        trunc_fn = TruncHour
        date_format = '%b %d %I%p'
    elif period == '15d':
        start_time = now - timedelta(days=15)
        trunc_fn = TruncDate
        date_format = '%b %d'
    elif period == '30d':
        start_time = now - timedelta(days=30)
        trunc_fn = TruncDate
        date_format = '%b %d'
    else:  # 7d default
        start_time = now - timedelta(days=7)
        trunc_fn = TruncDate
        date_format = '%b %d'

    unique_visitors = UniqueVisitorLog.objects.filter(created_at__gte=start_time).values('ip_address').distinct().count()
    product_views = AnalyticsEvent.objects.filter(event_type='product_view', timestamp__gte=start_time).count()
    search_queries = SearchQuery.objects.filter(timestamp__gte=start_time).count()
    add_to_cart_events = AnalyticsEvent.objects.filter(event_type='add_to_cart', timestamp__gte=start_time).count()
    checkout_starts = AnalyticsEvent.objects.filter(event_type='checkout_start', timestamp__gte=start_time).count()
    completed_orders = Order.objects.filter(status='Delivered', created_at__gte=start_time).count()
    all_orders = Order.objects.filter(created_at__gte=start_time).count()

    paid_orders = Order.objects.filter(status='Delivered', created_at__gte=start_time)
    paid_rev = paid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    all_time_revenue = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    avg_paid_order = paid_orders.aggregate(Avg('total_amount'))['total_amount__avg'] or Decimal('0.00')

    visitor_to_purchase_rate = round((all_orders / unique_visitors * 100), 1) if unique_visitors > 0 else 0.0
    abandoned_carts = max(0, add_to_cart_events - all_orders)

    # 1. Traffic Chart (Unique visitors over time)
    traffic_qs = UniqueVisitorLog.objects.filter(created_at__gte=start_time).annotate(t=trunc_fn('created_at')).values('t').annotate(c=Count('id')).order_by('t')
    chart_labels = [item['t'].strftime(date_format) for item in traffic_qs]
    chart_data = [item['c'] for item in traffic_qs]

    # 2. Revenue & Orders Over Time
    rev_qs = Order.objects.filter(status='Delivered', created_at__gte=start_time).annotate(t=trunc_fn('created_at')).values('t').annotate(total=Sum('total_amount')).order_by('t')
    rev_labels = [item['t'].strftime(date_format) for item in rev_qs]
    rev_data = [float(item['total']) for item in rev_qs]

    # 3. Order Status Distribution (Pie Chart)
    status_qs = Order.objects.filter(created_at__gte=start_time).values('status').annotate(count=Count('id'))
    status_labels = [s['status'] for s in status_qs]
    status_data = [s['count'] for s in status_qs]

    # 4. Device and Browser Breakdown (From AnalyticsEvent)
    device_qs = AnalyticsEvent.objects.filter(timestamp__gte=start_time).values('device_type').annotate(c=Count('id'))
    device_labels = [d['device_type'] or 'Desktop' for d in device_qs]
    device_data = [d['c'] for d in device_qs]

    # 5. Top Viewed & Ordered Products
    clicked_products = Product.objects.filter(views_count__gt=0).order_by('-views_count')[:6]
    clicked_labels = [p.name[:16] for p in clicked_products]
    clicked_data = [p.views_count for p in clicked_products]

    ordered_items = OrderItem.objects.filter(order__created_at__gte=start_time).values('product_name').annotate(qty=Sum('quantity')).order_by('-qty')[:6]
    order_labels = [item['product_name'][:16] if item['product_name'] else 'Item' for item in ordered_items]
    order_data = [item['qty'] for item in ordered_items]

    # 6. Districts
    districts = Order.objects.filter(created_at__gte=start_time).values('district').annotate(c=Count('id')).order_by('-c')[:6]
    district_labels = [d['district'] for d in districts]
    district_data = [d['c'] for d in districts]

    # 7. Sales Funnel Data
    funnel_labels = ['Unique Visitors', 'Product Views', 'Add to Cart', 'Checkout Started', 'Orders Completed']
    funnel_data = [unique_visitors, product_views, add_to_cart_events, checkout_starts, completed_orders]

    return render(request, 'merchant/analytics.html', {
        'period': period,
        'unique_visitors': unique_visitors,
        'product_views': product_views,
        'search_queries': search_queries,
        'add_to_cart_events': add_to_cart_events,
        'checkout_starts': checkout_starts,
        'completed_orders': completed_orders,
        'paid_orders': paid_orders.count(),
        'paid_rev': paid_rev,
        'all_time_revenue': all_time_revenue,
        'avg_paid_order': round(avg_paid_order, 2),
        'visitor_to_purchase_rate': visitor_to_purchase_rate,
        'abandoned_carts': abandoned_carts,
        
        # Charts JSON
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'rev_labels': json.dumps(rev_labels),
        'rev_data': json.dumps(rev_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'device_labels': json.dumps(device_labels),
        'device_data': json.dumps(device_data),
        'clicked_labels': json.dumps(clicked_labels),
        'clicked_data': json.dumps(clicked_data),
        'order_labels': json.dumps(order_labels),
        'order_data': json.dumps(order_data),
        'district_labels': json.dumps(district_labels),
        'district_data': json.dumps(district_data),
        'funnel_labels': json.dumps(funnel_labels),
        'funnel_data': json.dumps(funnel_data),
        'active_menu': 'analytics',
    })

# Promo Codes
@login_required(login_url='admin_login')
def merchant_promos(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        disc_type = request.POST.get('discount_type', 'percentage')
        disc_val = int(request.POST.get('discount_value', 10))
        max_disc = request.POST.get('max_discount') or None
        min_purch = request.POST.get('min_purchase') or None
        expiry = request.POST.get('expiry_date') or None

        if code:
            PromoCode.objects.create(
                code=code, discount_type=disc_type, discount_value=disc_val,
                max_discount=max_disc, min_purchase=min_purch, expiry_date=expiry
            )
            messages.success(request, f'Promo code "{code}" created successfully!')
        return redirect('merchant_promos')

    promos = PromoCode.objects.all().order_by('-created_at')
    return render(request, 'merchant/promo.html', {'promos': promos, 'active_menu': 'promo'})

@login_required(login_url='admin_login')
@require_POST
def toggle_promo(request, pk):
    p = get_object_or_404(PromoCode, pk=pk)
    p.is_active = not p.is_active
    p.save(update_fields=['is_active'])
    return redirect('merchant_promos')

@login_required(login_url='admin_login')
@require_POST
def delete_promo(request, pk):
    p = get_object_or_404(PromoCode, pk=pk)
    p.delete()
    messages.success(request, 'Promo code deleted successfully!')
    return redirect('merchant_promos')
"""

# -------------------------------------------------------------
# 5. TEMPLATES (MERCHANT ADMIN PANEL)
# -------------------------------------------------------------
FILES["templates/admin_custom/login.html"] = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Staff Portal Login - {{ site_setting.site_name }}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>body { font-family: 'Plus Jakarta Sans', sans-serif; }</style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex items-center justify-center p-4">
  <div class="w-full max-w-md">
    <div class="text-center mb-8">
      <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-purple-600 text-white font-black text-2xl shadow-xl shadow-purple-500/20 mb-3">
        FT
      </div>
      <h1 class="text-2xl font-black text-white">{{ site_setting.site_name }}</h1>
      <p class="text-xs text-slate-400 mt-1">Merchant Administration Portal</p>
    </div>

    <div class="bg-slate-800/80 backdrop-blur-md border border-slate-700/80 rounded-3xl p-8 shadow-2xl">
      {% if messages %}
      <div class="mb-5 space-y-2">
        {% for message in messages %}
        <div class="p-3.5 rounded-xl text-xs font-semibold text-center {% if 'error' in message.tags %}bg-rose-500/10 border border-rose-500/20 text-rose-400{% else %}bg-emerald-500/10 border border-emerald-500/20 text-emerald-400{% endif %}">
          {{ message }}
        </div>
        {% endfor %}
      </div>
      {% endif %}

      <form method="POST" action="{% url 'admin_login' %}" class="space-y-4">
        {% csrf_token %}
        <div>
          <label class="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Username</label>
          <input type="text" name="username" required placeholder="Enter username" class="w-full bg-slate-900/60 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-purple-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Password</label>
          <input type="password" name="password" required placeholder="••••••••" class="w-full bg-slate-900/60 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-purple-500">
        </div>
        <button type="submit" class="w-full py-3.5 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl text-sm transition shadow-lg shadow-purple-600/30">
          Sign In to Merchant Hub
        </button>
      </form>
    </div>
    <p class="text-center text-xs text-slate-500 mt-6">&copy; 2026 {{ site_setting.site_name }}. Secure Gateway.</p>
  </div>
</body>
</html>
"""

FILES["templates/merchant/base_merchant.html"] = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Merchant Portal - {{ site_setting.site_name }}{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    .btn-purple { background-color: #5B21B6; color: white; }
    .btn-purple:hover { background-color: #4C1D95; }
    .active-nav { background-color: #EDE9FE; color: #5B21B6; font-weight: 700; }
  </style>
</head>
<body class="bg-[#F8FAFC] text-slate-800 flex h-screen overflow-hidden">
  <!-- Toast Notification Container -->
  <div id="toastContainer" class="fixed top-5 right-5 z-50 space-y-2 pointer-events-none">
    {% if messages %}
      {% for message in messages %}
      <div class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl shadow-xl text-sm font-semibold transition-all duration-300 {% if 'error' in message.tags %}bg-rose-600 text-white{% else %}bg-emerald-600 text-white{% endif %}">
        <i class="fa-solid {% if 'error' in message.tags %}fa-circle-exclamation{% else %}fa-circle-check{% endif %}"></i>
        <span>{{ message }}</span>
      </div>
      {% endfor %}
    {% endif %}
  </div>

  <!-- Global Destructive Action Confirmation Modal -->
  <div id="confirmModal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl w-full max-w-sm p-6 shadow-2xl text-center space-y-4">
      <div class="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto text-xl">
        <i class="fa-solid fa-triangle-exclamation"></i>
      </div>
      <h3 class="text-base font-bold text-slate-900">Confirm Action</h3>
      <p id="confirmModalText" class="text-xs text-slate-500">Are you sure you want to delete this item? This action cannot be undone.</p>
      <form id="confirmModalForm" method="POST" action="" class="flex gap-2.5 pt-2">
        {% csrf_token %}
        <button type="button" onclick="closeConfirmModal()" class="flex-1 py-2.5 border rounded-xl font-bold text-xs text-slate-600 hover:bg-slate-50">Cancel</button>
        <button type="submit" class="flex-1 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-bold text-xs shadow-md">Confirm</button>
      </form>
    </div>
  </div>

  <!-- Sidebar -->
  <aside class="w-64 bg-white border-r border-slate-200 flex flex-col justify-between overflow-y-auto shrink-0">
    <div>
      <div class="h-20 flex items-center px-6 border-b border-slate-100 gap-3">
        <div class="w-10 h-10 rounded-xl bg-purple-600 text-white flex items-center justify-center font-black text-lg">
          FT
        </div>
        <div>
          <span class="text-base font-black tracking-tight text-slate-900 block uppercase leading-none">
            {{ site_setting.site_name }}
          </span>
          <span class="text-[10px] text-purple-600 font-bold uppercase tracking-wider">Merchant Hub</span>
        </div>
      </div>
      <nav class="p-4 space-y-1 text-xs text-slate-600 font-semibold">
        <a href="{% url 'merchant_dashboard' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'dashboard' %}active-nav{% endif %}">
          <i class="fa-solid fa-chart-pie w-4 text-sm"></i> Dashboard
        </a>
        <a href="{% url 'merchant_orders' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'orders' %}active-nav{% endif %}">
          <i class="fa-solid fa-cart-shopping w-4 text-sm"></i> Orders
        </a>
        <a href="{% url 'merchant_products' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'products' %}active-nav{% endif %}">
          <i class="fa-solid fa-box w-4 text-sm"></i> Products
        </a>
        <a href="{% url 'merchant_categories' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'categories' %}active-nav{% endif %}">
          <i class="fa-solid fa-layer-group w-4 text-sm"></i> Categories
        </a>
        <a href="{% url 'merchant_sections' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'sections' %}active-nav{% endif %}">
          <i class="fa-solid fa-table-cells-large w-4 text-sm"></i> Homepage Sections
        </a>
        <a href="{% url 'merchant_customers' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'customers' %}active-nav{% endif %}">
          <i class="fa-solid fa-users w-4 text-sm"></i> Customers
        </a>
        <a href="{% url 'merchant_promos' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'promo' %}active-nav{% endif %}">
          <i class="fa-solid fa-ticket w-4 text-sm"></i> Promo Codes
        </a>
        <a href="{% url 'merchant_analytics' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'analytics' %}active-nav{% endif %}">
          <i class="fa-solid fa-chart-line w-4 text-sm"></i> Analytics Engine
        </a>
        <a href="{% url 'merchant_customize_theme' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'themes' %}active-nav{% endif %}">
          <i class="fa-solid fa-palette w-4 text-sm"></i> Customize Theme
        </a>
        <a href="{% url 'merchant_settings' %}" class="flex items-center gap-3 px-3.5 py-3 rounded-xl hover:bg-slate-100 {% if active_menu == 'settings' %}active-nav{% endif %}">
          <i class="fa-solid fa-gear w-4 text-sm"></i> Site Settings
        </a>
      </nav>
    </div>
    <div class="p-4 border-t border-slate-100">
      <a href="/" target="_blank" class="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition">
        <i class="fa-solid fa-arrow-up-right-from-square"></i> View Live Store
      </a>
    </div>
  </aside>

  <!-- Main Content Area -->
  <div class="flex-1 flex flex-col overflow-y-auto">
    <header class="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
      <div class="flex items-center gap-4">
        <span class="text-xs font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
          ● Store Operational
        </span>
      </div>
      <div class="flex items-center gap-6">
        <div class="text-right hidden sm:block">
          <p class="text-xs font-bold text-slate-900">{{ request.user.username|title|default:"Staff Admin" }}</p>
          <p class="text-[10px] text-slate-400 font-semibold">{{ site_setting.site_name }} Master Control</p>
        </div>
        <a href="{% url 'admin_logout' %}" title="Logout" class="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-sm hover:bg-rose-100 transition">
          <i class="fa-solid fa-power-off text-sm"></i>
        </a>
      </div>
    </header>
    <main class="p-8">
      {% block content %}{% endblock %}
    </main>
  </div>

  <script>
    function triggerActionModal(actionUrl, message) {
      document.getElementById('confirmModalForm').action = actionUrl;
      document.getElementById('confirmModalText').innerText = message || "Are you sure you want to execute this action?";
      document.getElementById('confirmModal').classList.remove('hidden');
    }
    function closeConfirmModal() {
      document.getElementById('confirmModal').classList.add('hidden');
    }
    setTimeout(() => {
      const toasts = document.getElementById('toastContainer');
      if (toasts) toasts.style.display = 'none';
    }, 4500);
  </script>
</body>
</html>
"""

FILES["templates/merchant/dashboard.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Dashboard - Store Overview{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto space-y-8">
  <div>
    <h1 class="text-2xl font-black text-slate-900">Dashboard & Store Performance</h1>
    <p class="text-xs text-slate-500 mt-1">Real-time overview of revenue, operations and traffic</p>
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl shrink-0">
        <i class="fa-solid fa-bangladeshi-taka-sign"></i>
      </div>
      <div>
        <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Gross Sales</div>
        <div class="text-2xl font-black text-slate-900 mt-0.5">৳ {{ total_sales }}</div>
      </div>
    </div>

    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl shrink-0">
        <i class="fa-solid fa-cart-shopping"></i>
      </div>
      <div>
        <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Orders</div>
        <div class="text-2xl font-black text-slate-900 mt-0.5">{{ total_orders }}</div>
      </div>
    </div>

    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center text-xl shrink-0">
        <i class="fa-solid fa-box"></i>
      </div>
      <div>
        <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Inventory Items</div>
        <div class="text-2xl font-black text-slate-900 mt-0.5">{{ total_products }}</div>
      </div>
    </div>

    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl shrink-0">
        <i class="fa-solid fa-users"></i>
      </div>
      <div>
        <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Unique Visitors</div>
        <div class="text-2xl font-black text-slate-900 mt-0.5">{{ total_visitors }}</div>
      </div>
    </div>
  </div>

  <div class="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
    <div class="p-6 border-b border-slate-100 flex justify-between items-center">
      <h3 class="font-bold text-slate-900 text-base">Recent Orders</h3>
      <a href="{% url 'merchant_orders' %}" class="text-xs font-bold text-purple-600 hover:underline">View All Orders &rarr;</a>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs text-slate-600">
        <thead class="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold">
          <tr>
            <th class="p-4">Order ID</th>
            <th class="p-4">Customer</th>
            <th class="p-4">Location</th>
            <th class="p-4">Amount</th>
            <th class="p-4">Status</th>
            <th class="p-4">Date</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          {% for order in recent_orders %}
          <tr class="hover:bg-slate-50/50">
            <td class="p-4 font-mono font-bold text-purple-700">{{ order.order_id }}</td>
            <td class="p-4 font-semibold text-slate-900">{{ order.customer_name }}</td>
            <td class="p-4">{{ order.district }}</td>
            <td class="p-4 font-bold text-slate-900">৳ {{ order.total_amount }}</td>
            <td class="p-4">
              <span class="px-2.5 py-1 text-[10px] font-bold rounded-full bg-slate-100 text-slate-700">
                {{ order.status }}
              </span>
            </td>
            <td class="p-4 text-slate-400">{{ order.created_at|date:"M d, H:i" }}</td>
          </tr>
          {% empty %}
          <tr><td colspan="6" class="p-8 text-center text-slate-400">No orders placed yet.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
"""

FILES["templates/merchant/orders.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Orders Management{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto space-y-6">
  <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
    <div>
      <h1 class="text-2xl font-black text-slate-900">Orders Management</h1>
      <p class="text-xs text-slate-400 mt-1">Review orders, update statuses and inspect deliveries</p>
    </div>
    <a href="{% url 'export_orders_csv' %}" class="bg-white border border-slate-200 px-4 py-2.5 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition flex items-center gap-2 shadow-sm">
      <i class="fa-solid fa-file-csv text-emerald-600"></i> Export CSV
    </a>
  </div>

  <!-- Search & Bulk Update Bar -->
  <div class="bg-white p-4 rounded-3xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-center">
    <form method="GET" class="relative w-full md:w-80">
      <input type="text" name="q" value="{{ search_query|default:'' }}" placeholder="Search Order ID, Phone..." class="w-full border rounded-xl pl-9 pr-4 py-2 text-xs bg-slate-50 focus:outline-none focus:border-purple-600">
      <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
    </form>

    <!-- Bulk Action Form -->
    <form id="bulkOrderForm" method="POST" action="{% url 'bulk_order_action' %}" class="flex items-center gap-2 w-full md:w-auto">
      {% csrf_token %}
      <span class="text-xs font-semibold text-slate-400 whitespace-nowrap">Bulk Update:</span>
      <select name="bulk_action" required class="border rounded-xl px-3 py-1.5 text-xs bg-slate-50 outline-none">
        <option value="">Select Status Action</option>
        <option value="Confirmed">Mark as Confirmed</option>
        <option value="Shipped">Mark as Shipped</option>
        <option value="Delivered">Mark as Delivered</option>
        <option value="Cancelled">Mark as Cancelled</option>
        <option value="delete">Delete Selected</option>
      </select>
      <button type="submit" class="bg-purple-600 text-white px-4 py-1.5 rounded-xl text-xs font-bold hover:bg-purple-700 transition">
        Apply
      </button>
    </form>
  </div>

  <!-- Order Table -->
  <div class="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs text-slate-600">
        <thead class="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold border-b">
          <tr>
            <th class="p-4 w-10"><input type="checkbox" id="selectAllOrders" onclick="toggleAllOrderCheckboxes(this)"></th>
            <th class="p-4">Order ID & Date</th>
            <th class="p-4">Customer</th>
            <th class="p-4">Address & Items</th>
            <th class="p-4">Total</th>
            <th class="p-4">Status & Timeline</th>
            <th class="p-4 text-right">Update</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          {% for order in orders %}
          <tr class="hover:bg-slate-50/50">
            <td class="p-4">
              <input type="checkbox" name="selected_orders" value="{{ order.id }}" form="bulkOrderForm" class="order-checkbox">
            </td>
            <td class="p-4">
              <span class="font-mono font-black text-purple-700 block">{{ order.order_id }}</span>
              <span class="text-[10px] text-slate-400">{{ order.created_at|date:"M d, Y H:i" }}</span>
            </td>
            <td class="p-4 font-semibold text-slate-900">
              <div>{{ order.customer_name }}</div>
              <div class="text-[10px] text-slate-400 font-mono">{{ order.customer_phone }}</div>
            </td>
            <td class="p-4 max-w-xs">
              <div class="line-clamp-1 font-semibold text-slate-800">{{ order.district }} ({{ order.thana|default:"-" }})</div>
              <div class="text-[10px] text-slate-400 line-clamp-1">{{ order.shipping_address }}</div>
              <div class="text-[10px] text-purple-600 mt-0.5 font-bold">{{ order.items.count }} Item(s)</div>
            </td>
            <td class="p-4 font-black text-slate-900">
              ৳ {{ order.total_amount }}
              {% if order.discount_amount > 0 %}
              <div class="text-[9px] text-emerald-600 font-bold">-৳{{ order.discount_amount }} Promo</div>
              {% endif %}
            </td>
            <td class="p-4">
              <!-- Visual Status Badge -->
              <span class="inline-block px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider
                {% if order.status == 'Delivered' %}bg-emerald-100 text-emerald-800
                {% elif order.status == 'Shipped' %}bg-blue-100 text-blue-800
                {% elif order.status == 'Confirmed' %}bg-purple-100 text-purple-800
                {% elif order.status == 'Cancelled' %}bg-rose-100 text-rose-800
                {% else %}bg-amber-100 text-amber-800{% endif %}">
                {{ order.status }}
              </span>
            </td>
            <td class="p-4 text-right">
              <form method="POST" action="{% url 'update_order_status' order.pk %}" class="inline-flex">
                {% csrf_token %}
                <select name="status" onchange="this.form.submit()" class="border rounded-lg px-2 py-1 text-[11px] bg-slate-50 outline-none font-semibold">
                  <option value="" disabled selected>Change Status</option>
                  <option value="Placed">Placed</option>
                  <option value="Confirmed">Confirmed</option>
                  <option value="Shipped">Shipped</option>
                  <option value="Delivered">Delivered</option>
                  <option value="Cancelled">Cancelled</option>
                  <option value="Returned">Returned</option>
                </select>
              </form>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="7" class="p-12 text-center text-slate-400">No orders matching criteria found.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    {% if orders.has_other_pages %}
    <div class="p-4 border-t flex justify-between items-center text-xs text-slate-500">
      <span>Page {{ orders.number }} of {{ orders.paginator.num_pages }}</span>
      <div class="flex gap-1">
        {% if orders.has_previous %}
        <a href="?page={{ orders.previous_page_number }}&q={{ search_query }}" class="px-3 py-1.5 border rounded-lg hover:bg-slate-50 font-bold">&larr; Prev</a>
        {% endif %}
        {% if orders.has_next %}
        <a href="?page={{ orders.next_page_number }}&q={{ search_query }}" class="px-3 py-1.5 border rounded-lg hover:bg-slate-50 font-bold">Next &rarr;</a>
        {% endif %}
      </div>
    </div>
    {% endif %}
  </div>
</div>

<script>
  function toggleAllOrderCheckboxes(master) {
    document.querySelectorAll('.order-checkbox').forEach(cb => cb.checked = master.checked);
  }
</script>
{% endblock %}
"""

FILES["templates/merchant/products.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Products Inventory{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-2xl font-black text-slate-900">Product Inventory</h1>
      <p class="text-xs text-slate-400 mt-1">Manage mobile covers, key rings and inventory levels</p>
    </div>
    <button onclick="document.getElementById('productModal').classList.remove('hidden')" class="btn-purple px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm">
      <i class="fa-solid fa-plus"></i> Add Product
    </button>
  </div>

  <!-- Search & Bulk Update Bar -->
  <div class="bg-white p-4 rounded-3xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-center">
    <form method="GET" class="relative w-full md:w-80">
      <input type="text" name="q" value="{{ search_query|default:'' }}" placeholder="Search products..." class="w-full border rounded-xl pl-9 pr-4 py-2 text-xs bg-slate-50 focus:outline-none focus:border-purple-600">
      <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
    </form>

    <form id="bulkProdForm" method="POST" action="{% url 'bulk_product_action' %}" class="flex items-center gap-2 w-full md:w-auto">
      {% csrf_token %}
      <span class="text-xs font-semibold text-slate-400 whitespace-nowrap">Bulk Actions:</span>
      <select name="bulk_action" required class="border rounded-xl px-3 py-1.5 text-xs bg-slate-50 outline-none">
        <option value="">Select Action</option>
        <option value="activate">Activate Selected</option>
        <option value="deactivate">Deactivate Selected</option>
        <option value="delete">Delete Selected</option>
      </select>
      <button type="submit" class="bg-purple-600 text-white px-4 py-1.5 rounded-xl text-xs font-bold hover:bg-purple-700 transition">
        Apply
      </button>
    </form>
  </div>

  <div class="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs text-slate-600">
        <thead class="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold border-b">
          <tr>
            <th class="p-4 w-10"><input type="checkbox" id="selectAllProds" onclick="toggleAllProdCheckboxes(this)"></th>
            <th class="p-4">Item</th>
            <th class="p-4">Category</th>
            <th class="p-4">Price / Offer</th>
            <th class="p-4">Stock Status</th>
            <th class="p-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          {% for product in products %}
          <tr class="hover:bg-slate-50/50">
            <td class="p-4">
              <input type="checkbox" name="selected_products" value="{{ product.id }}" form="bulkProdForm" class="prod-checkbox">
            </td>
            <td class="p-4 flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-slate-100 border overflow-hidden shrink-0 flex items-center justify-center">
                {% if product.image %}
                <img src="{{ product.image.url }}" class="w-full h-full object-cover">
                {% else %}
                <i class="fa-solid fa-box text-slate-300"></i>
                {% endif %}
              </div>
              <div>
                <a href="{% url 'product_detail' product.pk %}" target="_blank" class="font-bold text-slate-900 hover:text-purple-600 line-clamp-1">
                  {{ product.name }}
                </a>
                <span class="text-[10px] text-slate-400">Views: {{ product.views_count }}</span>
              </div>
            </td>
            <td class="p-4 font-semibold text-slate-700">{{ product.category.name|default:"Uncategorized" }}</td>
            <td class="p-4">
              <span class="font-black text-slate-900 block">৳ {{ product.effective_price }}</span>
              {% if product.discount_price and product.discount_price < product.price %}
              <span class="text-[10px] text-slate-400 line-through">৳ {{ product.price }}</span>
              {% endif %}
            </td>
            <td class="p-4">
              {% if product.stock > 0 %}
              <span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                In Stock ({{ product.stock }})
              </span>
              {% else %}
              <span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                Out of Stock (0)
              </span>
              {% endif %}
            </td>
            <td class="p-4 text-right space-x-2">
              <a href="{% url 'merchant_edit_product' product.pk %}" class="p-2 text-slate-400 hover:text-purple-600 transition inline-block">
                <i class="fa-solid fa-pen"></i>
              </a>
              <button type="button" onclick="triggerActionModal('{% url 'merchant_delete_product' product.pk %}', 'Delete product {{ product.name|escapejs }}?')" class="p-2 text-slate-400 hover:text-rose-600 transition inline-block">
                <i class="fa-regular fa-trash-can"></i>
              </button>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="6" class="p-12 text-center text-slate-400">No products found. Add your first item!</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- Modal: Add Product with Image Validation -->
<div id="productModal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-3xl w-full max-w-2xl p-6 shadow-2xl max-h-[90vh] overflow-y-auto space-y-4">
    <div class="flex justify-between items-center border-b pb-3">
      <h3 class="font-bold text-slate-900 text-base">Add New Product</h3>
      <button onclick="document.getElementById('productModal').classList.add('hidden')" class="text-slate-400 text-xl">&times;</button>
    </div>
    <form method="POST" action="{% url 'add_product' %}" enctype="multipart/form-data" class="space-y-4">
      {% csrf_token %}
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Product Title *</label>
          <input type="text" name="name" required placeholder="e.g. Leather Phone Case" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Category *</label>
          <select name="category" required class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
            {% for cat in categories %}
            <option value="{{ cat.id }}">{{ cat.name }}</option>
            {% endfor %}
          </select>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Regular Price (৳) *</label>
          <input type="number" step="0.01" name="price" required class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Offer Price (৳)</label>
          <input type="number" step="0.01" name="discount_price" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Stock Quantity *</label>
          <input type="number" name="stock" value="50" required class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
        </div>
      </div>

      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Main Image (JPG, PNG, WebP &le; 5MB)</label>
        <input type="file" name="main_image" accept="image/*" class="w-full text-xs text-slate-500 border rounded-xl p-2 bg-slate-50">
      </div>

      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Description</label>
        <textarea name="description" rows="3" class="w-full border rounded-xl p-3 text-xs bg-slate-50 outline-none"></textarea>
      </div>

      <div class="flex gap-2 pt-2">
        <button type="button" onclick="document.getElementById('productModal').classList.add('hidden')" class="flex-1 py-2.5 border rounded-xl font-bold text-xs">Cancel</button>
        <button type="submit" class="flex-1 py-2.5 btn-purple rounded-xl font-bold text-xs shadow-md">Save Product</button>
      </div>
    </form>
  </div>
</div>

<script>
  function toggleAllProdCheckboxes(master) {
    document.querySelectorAll('.prod-checkbox').forEach(cb => cb.checked = master.checked);
  }
</script>
{% endblock %}
"""

FILES["templates/merchant/categories.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Categories Control{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-2xl font-black text-slate-900">Categories & Collections</h1>
      <p class="text-xs text-slate-400 mt-1">Organize your store's catalog and sub-categories</p>
    </div>
    <button onclick="document.getElementById('catModal').classList.remove('hidden')" class="btn-purple px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm">
      <i class="fa-solid fa-plus"></i> Add Category
    </button>
  </div>

  <div class="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
    <table class="w-full text-left text-xs text-slate-600">
      <thead class="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold border-b">
        <tr>
          <th class="p-4">Visual</th>
          <th class="p-4">Name</th>
          <th class="p-4">Subcategories</th>
          <th class="p-4">Status</th>
          <th class="p-4 text-right">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        {% for cat in categories %}
        <tr class="hover:bg-slate-50/50">
          <td class="p-4 w-16">
            <div class="w-10 h-10 rounded-xl bg-slate-100 border overflow-hidden flex items-center justify-center">
              {% if cat.image %}<img src="{{ cat.image.url }}" class="w-full h-full object-cover">
              {% else %}<i class="fa-solid fa-folder text-slate-300"></i>{% endif %}
            </div>
          </td>
          <td class="p-4 font-bold text-slate-900">
            <a href="{% url 'merchant_category_detail' cat.pk %}" class="hover:text-purple-600">{{ cat.name }}</a>
          </td>
          <td class="p-4 font-semibold text-slate-700">{{ cat.subcategories.count }} Subcategory(ies)</td>
          <td class="p-4">
            <form method="POST" action="{% url 'merchant_toggle_category' cat.pk %}" class="inline">
              {% csrf_token %}
              <button type="submit" class="p-1 text-base {% if cat.is_active %}text-emerald-600{% else %}text-slate-300{% endif %}">
                <i class="fa-solid fa-toggle-on"></i>
              </button>
            </form>
          </td>
          <td class="p-4 text-right space-x-2">
            <a href="{% url 'merchant_category_detail' cat.pk %}" class="p-1.5 text-slate-400 hover:text-purple-600"><i class="fa-solid fa-pen"></i></a>
            <button type="button" onclick="triggerActionModal('{% url 'merchant_delete_category' cat.pk %}', 'Delete category {{ cat.name|escapejs }}?')" class="p-1.5 text-slate-400 hover:text-rose-600">
              <i class="fa-regular fa-trash-can"></i>
            </button>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="5" class="p-12 text-center text-slate-400">No categories added yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<div id="catModal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-3xl w-full max-w-md p-6 shadow-2xl space-y-4">
    <div class="flex justify-between items-center border-b pb-3">
      <h3 class="font-bold text-slate-900 text-base">Create Category</h3>
      <button onclick="document.getElementById('catModal').classList.add('hidden')" class="text-slate-400 text-xl">&times;</button>
    </div>
    <form method="POST" enctype="multipart/form-data" class="space-y-4">
      {% csrf_token %}
      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Category Name *</label>
        <input type="text" name="name" required class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Category Thumbnail</label>
        <input type="file" name="image" accept="image/*" class="w-full text-xs border rounded-xl p-2 bg-slate-50">
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Short Description</label>
        <textarea name="short_description" rows="2" class="w-full border rounded-xl p-3 text-xs bg-slate-50 outline-none"></textarea>
      </div>
      <div class="flex gap-2 pt-2">
        <button type="button" onclick="document.getElementById('catModal').classList.add('hidden')" class="flex-1 py-2 border rounded-xl font-bold text-xs">Cancel</button>
        <button type="submit" class="flex-1 py-2 btn-purple rounded-xl font-bold text-xs shadow-md">Create</button>
      </div>
    </form>
  </div>
</div>
{% endblock %}
"""

FILES["templates/merchant/category_detail.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}{{ category.name }} - Details{% endblock %}
{% block content %}
<div class="max-w-5xl mx-auto space-y-6">
  <div class="flex items-center gap-3">
    <a href="{% url 'merchant_categories' %}" class="w-8 h-8 rounded-full border flex items-center justify-center text-slate-500 hover:bg-slate-100">&larr;</a>
    <h1 class="text-xl font-black text-slate-900">Category &gt; <span class="text-purple-600">{{ category.name }}</span></h1>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
      <h3 class="font-bold text-slate-900 text-sm">Edit Category Information</h3>
      <form method="POST" enctype="multipart/form-data" class="space-y-4">
        {% csrf_token %}
        <input type="hidden" name="action" value="update_category">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Category Name</label>
          <input type="text" name="name" value="{{ category.name }}" required class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Description</label>
          <textarea name="short_description" rows="3" class="w-full border rounded-xl p-3 text-xs bg-slate-50 outline-none">{{ category.short_description|default:'' }}</textarea>
        </div>
        <button type="submit" class="w-full py-2.5 btn-purple rounded-xl text-xs font-bold shadow-md">Save Changes</button>
      </form>
    </div>

    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
      <h3 class="font-bold text-slate-900 text-sm">Sub-categories ({{ subcategories.count }})</h3>
      <div class="space-y-2">
        {% for sub in subcategories %}
        <div class="flex justify-between items-center p-3 rounded-2xl bg-slate-50 border text-xs">
          <span class="font-bold text-slate-800">{{ sub.name }}</span>
          <button type="button" onclick="triggerActionModal('{% url 'merchant_delete_category' sub.pk %}', 'Delete subcategory {{ sub.name|escapejs }}?')" class="text-rose-600 font-bold">Delete</button>
        </div>
        {% empty %}
        <p class="text-xs text-slate-400 py-4">No subcategories created yet.</p>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

FILES["templates/merchant/sections.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Showcase Sections{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-2xl font-black text-slate-900">Homepage Showcase Sections</h1>
      <p class="text-xs text-slate-400 mt-1">Configure Flash Sales, Featured Drops and Custom Sections</p>
    </div>
    <button onclick="document.getElementById('secModal').classList.remove('hidden')" class="btn-purple px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm">
      <i class="fa-solid fa-plus"></i> Create Section
    </button>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    {% for sec in sections %}
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
      <div class="flex justify-between items-start">
        <div>
          <span class="text-[10px] font-bold px-2.5 py-1 rounded-full uppercase bg-slate-100 text-slate-700">{{ sec.get_background_style_display }}</span>
          <h3 class="text-lg font-black text-slate-900 mt-2">{{ sec.title }}</h3>
          {% if sec.has_countdown and sec.end_time %}
          <div class="text-xs text-rose-600 font-bold mt-1 flex items-center gap-1.5">
            <i class="fa-regular fa-clock"></i> Ends: {{ sec.end_time|date:"M d, Y H:i" }}
          </div>
          {% endif %}
        </div>
        <div class="flex items-center gap-2">
          <form method="POST" action="{% url 'merchant_toggle_section' sec.pk %}" class="inline">
            {% csrf_token %}
            <button type="submit" class="text-lg {% if sec.is_active %}text-purple-600{% else %}text-slate-300{% endif %}">
              <i class="fa-solid fa-toggle-on"></i>
            </button>
          </form>
          <button type="button" onclick="triggerActionModal('{% url 'merchant_delete_section' sec.pk %}', 'Delete section {{ sec.title|escapejs }}?')" class="text-slate-400 hover:text-rose-600">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </div>
      </div>
      <div class="text-xs text-slate-500 font-medium border-t pt-3">
        Assigned Products: <span class="font-bold text-slate-900">{{ sec.products.count }}</span>
      </div>
    </div>
    {% endfor %}
  </div>
</div>

<!-- Modal: Create Section with DateTime Countdown -->
<div id="secModal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-3xl w-full max-w-lg p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
    <div class="flex justify-between items-center border-b pb-3">
      <h3 class="font-bold text-slate-900 text-base">Create Showcase Section</h3>
      <button onclick="document.getElementById('secModal').classList.add('hidden')" class="text-slate-400 text-xl">&times;</button>
    </div>
    <form method="POST" class="space-y-4">
      {% csrf_token %}
      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Section Title *</label>
        <input type="text" name="title" required placeholder="e.g. Flash Sale" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Visual Theme</label>
        <select name="background_style" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
          <option value="light">White / Light Minimal</option>
          <option value="brown">Warm Coffee Brown</option>
          <option value="dark">Charcoal Black</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <input type="checkbox" name="has_countdown" id="cd_check" class="rounded text-purple-600">
        <label for="cd_check" class="text-xs font-bold text-slate-700">Enable Countdown Expiration</label>
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Countdown End Datetime</label>
        <input type="datetime-local" name="end_time" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Featured Products</label>
        <select name="products" multiple class="w-full border rounded-xl p-2 text-xs bg-slate-50 h-32 outline-none">
          {% for p in all_products %}
          <option value="{{ p.id }}">{{ p.name }} (৳{{ p.effective_price }})</option>
          {% endfor %}
        </select>
      </div>
      <div class="flex gap-2 pt-2">
        <button type="button" onclick="document.getElementById('secModal').classList.add('hidden')" class="flex-1 py-2 border rounded-xl font-bold text-xs">Cancel</button>
        <button type="submit" class="flex-1 py-2 btn-purple rounded-xl font-bold text-xs shadow-md">Save</button>
      </div>
    </form>
  </div>
</div>
{% endblock %}
"""

FILES["templates/merchant/customers.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Customers Directory{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-black text-slate-900">Customers Directory</h1>
    <p class="text-xs text-slate-400 mt-1">Insights on recurring clients, order counts and total spent</p>
  </div>

  <div class="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
    <table class="w-full text-left text-xs text-slate-600">
      <thead class="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold border-b">
        <tr>
          <th class="p-4">Customer Name</th>
          <th class="p-4">Phone Number</th>
          <th class="p-4">Orders Placed</th>
          <th class="p-4">Total Value</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        {% for c in customers %}
        <tr class="hover:bg-slate-50/50">
          <td class="p-4 font-bold text-slate-900">{{ c.customer_name }}</td>
          <td class="p-4 font-mono font-semibold">{{ c.customer_phone }}</td>
          <td class="p-4 font-semibold text-purple-600">{{ c.orders_count }} order(s)</td>
          <td class="p-4 font-black text-slate-900">৳ {{ c.total_spent }}</td>
        </tr>
        {% empty %}
        <tr><td colspan="4" class="p-12 text-center text-slate-400">No customer records yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
"""

FILES["templates/merchant/promo.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Promo Codes Control{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-2xl font-black text-slate-900">Promo & Discount Codes</h1>
      <p class="text-xs text-slate-400 mt-1">Create and manage checkout coupons for campaigns</p>
    </div>
    <button onclick="document.getElementById('promoModal').classList.remove('hidden')" class="btn-purple px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm">
      <i class="fa-solid fa-plus"></i> New Promo Code
    </button>
  </div>

  <div class="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
    <table class="w-full text-left text-xs text-slate-600">
      <thead class="bg-slate-50 text-slate-400 uppercase text-[10px] font-bold border-b">
        <tr>
          <th class="p-4">Code</th>
          <th class="p-4">Discount</th>
          <th class="p-4">Min Spend</th>
          <th class="p-4">Expiry</th>
          <th class="p-4">Status</th>
          <th class="p-4 text-right">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        {% for p in promos %}
        <tr class="hover:bg-slate-50/50">
          <td class="p-4 font-mono font-black text-purple-700">{{ p.code }}</td>
          <td class="p-4 font-bold text-slate-900">
            {% if p.discount_type == 'percentage' %}{{ p.discount_value }}% OFF{% else %}৳{{ p.discount_value }} Flat{% endif %}
          </td>
          <td class="p-4">৳ {{ p.min_purchase|default:"0.00" }}</td>
          <td class="p-4">{{ p.expiry_date|default:"No Expiry" }}</td>
          <td class="p-4">
            <form method="POST" action="{% url 'toggle_promo' p.pk %}" class="inline">
              {% csrf_token %}
              <button type="submit" class="text-base {% if p.is_active %}text-emerald-600{% else %}text-slate-300{% endif %}">
                <i class="fa-solid fa-toggle-on"></i>
              </button>
            </form>
          </td>
          <td class="p-4 text-right">
            <button type="button" onclick="triggerActionModal('{% url 'delete_promo' p.pk %}', 'Delete coupon {{ p.code }}?')" class="p-1.5 text-slate-400 hover:text-rose-600">
              <i class="fa-regular fa-trash-can"></i>
            </button>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="6" class="p-12 text-center text-slate-400">No active promo codes found.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<div id="promoModal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-3xl w-full max-w-md p-6 shadow-2xl space-y-4">
    <div class="flex justify-between items-center border-b pb-3">
      <h3 class="font-bold text-slate-900 text-base">New Coupon Code</h3>
      <button onclick="document.getElementById('promoModal').classList.add('hidden')" class="text-slate-400 text-xl">&times;</button>
    </div>
    <form method="POST" class="space-y-4">
      {% csrf_token %}
      <div>
        <label class="block text-xs font-bold text-slate-700 mb-1">Coupon Code *</label>
        <input type="text" name="code" required placeholder="e.g. SUMMER20" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none uppercase font-mono">
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Discount Type</label>
          <select name="discount_type" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
            <option value="percentage">Percentage (%)</option>
            <option value="fixed">Fixed Amount (৳)</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Value *</label>
          <input type="number" name="discount_value" value="10" required class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Min. Order Total (৳)</label>
          <input type="number" step="0.01" name="min_purchase" placeholder="0" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Expiry Date</label>
          <input type="date" name="expiry_date" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
        </div>
      </div>
      <div class="flex gap-2 pt-2">
        <button type="button" onclick="document.getElementById('promoModal').classList.add('hidden')" class="flex-1 py-2 border rounded-xl font-bold text-xs">Cancel</button>
        <button type="submit" class="flex-1 py-2 btn-purple rounded-xl font-bold text-xs shadow-md">Create</button>
      </div>
    </form>
  </div>
</div>
{% endblock %}
"""

FILES["templates/merchant/settings.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Site Settings{% endblock %}
{% block content %}
<div class="max-w-4xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-black text-slate-900">Site Settings & Contact Info</h1>
    <p class="text-xs text-slate-400 mt-1">Configure your official storefront numbers, address and shipping rates</p>
  </div>

  <div class="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
    <form method="POST" class="space-y-6">
      {% csrf_token %}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Brand Name</label>
          <input type="text" name="site_name" value="{{ setting.site_name }}" required class="w-full border rounded-xl px-4 py-2.5 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Helpline Phone</label>
          <input type="text" name="contact_phone" value="{{ setting.contact_phone }}" required class="w-full border rounded-xl px-4 py-2.5 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">WhatsApp Number</label>
          <input type="text" name="whatsapp_number" value="{{ setting.whatsapp_number }}" required class="w-full border rounded-xl px-4 py-2.5 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Contact Email</label>
          <input type="email" name="contact_email" value="{{ setting.contact_email }}" required class="w-full border rounded-xl px-4 py-2.5 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Delivery Fee (Inside Dhaka)</label>
          <input type="number" step="0.01" name="delivery_fee_dhaka" value="{{ setting.delivery_fee_dhaka }}" required class="w-full border rounded-xl px-4 py-2.5 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Delivery Fee (Outside Dhaka)</label>
          <input type="number" step="0.01" name="delivery_fee_outside" value="{{ setting.delivery_fee_outside }}" required class="w-full border rounded-xl px-4 py-2.5 text-xs bg-slate-50 outline-none">
        </div>
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Office / Shop Physical Address</label>
        <textarea name="office_address" rows="2" class="w-full border rounded-xl p-3 text-xs bg-slate-50 outline-none">{{ setting.office_address }}</textarea>
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Announcement Notice</label>
        <textarea name="announcement_notice" rows="2" class="w-full border rounded-xl p-3 text-xs bg-slate-50 outline-none">{{ setting.announcement_notice }}</textarea>
      </div>
      <button type="submit" class="btn-purple px-8 py-3 rounded-xl text-xs font-bold shadow-md">
        Save Settings
      </button>
    </form>
  </div>
</div>
{% endblock %}
"""

FILES["templates/merchant/customize_theme.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Customize Theme{% endblock %}
{% block content %}
<div class="max-w-3xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-black text-slate-900">Customize Theme & Brand Colors</h1>
    <p class="text-xs text-slate-400 mt-1">Live branding adjustments and storefront aesthetics</p>
  </div>

  <div class="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
    <form method="POST" class="space-y-6">
      {% csrf_token %}
      <div>
        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Primary Theme Brand Color</label>
        <div class="flex items-center gap-3">
          <input type="color" name="theme_color" value="{{ setting.theme_color }}" id="colorInput" class="w-12 h-12 rounded-xl border p-1 cursor-pointer" oninput="document.getElementById('colorHex').innerText = this.value">
          <span id="colorHex" class="font-mono text-sm font-bold text-slate-700">{{ setting.theme_color }}</span>
        </div>
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Storefront Mode</label>
        <select name="theme_mode" class="w-full border rounded-xl px-4 py-2.5 text-xs bg-slate-50 outline-none">
          <option value="light" {% if setting.theme_mode == 'light' %}selected{% endif %}>Light Mode (Standard)</option>
          <option value="dark" {% if setting.theme_mode == 'dark' %}selected{% endif %}>Dark Mode (Minimalist)</option>
        </select>
      </div>
      <button type="submit" class="btn-purple px-8 py-3 rounded-xl text-xs font-bold shadow-md">
        Save Theme Styles
      </button>
    </form>
  </div>
</div>
{% endblock %}
"""

FILES["templates/merchant/analytics.html"] = """{% extends 'merchant/base_merchant.html' %}
{% block title %}Analytics Engine - Fantacy Tech{% endblock %}
{% block content %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<div class="max-w-6xl mx-auto space-y-8">
  <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
    <div>
      <h1 class="text-2xl font-black text-slate-900">Business Intelligence & Analytics</h1>
      <p class="text-xs text-slate-400 mt-1">Real-time metrics, funnel conversions and customer patterns</p>
    </div>
    
    <!-- Time Period Filter -->
    <div class="flex items-center gap-1 bg-white p-1 rounded-2xl border shadow-sm text-xs font-bold">
      <a href="?period=12h" class="px-3 py-1.5 rounded-xl {% if period == '12h' %}bg-purple-600 text-white{% else %}text-slate-600 hover:bg-slate-100{% endif %}">12h</a>
      <a href="?period=24h" class="px-3 py-1.5 rounded-xl {% if period == '24h' %}bg-purple-600 text-white{% else %}text-slate-600 hover:bg-slate-100{% endif %}">24h</a>
      <a href="?period=48h" class="px-3 py-1.5 rounded-xl {% if period == '48h' %}bg-purple-600 text-white{% else %}text-slate-600 hover:bg-slate-100{% endif %}">48h</a>
      <a href="?period=7d" class="px-3 py-1.5 rounded-xl {% if period == '7d' %}bg-purple-600 text-white{% else %}text-slate-600 hover:bg-slate-100{% endif %}">7d</a>
      <a href="?period=15d" class="px-3 py-1.5 rounded-xl {% if period == '15d' %}bg-purple-600 text-white{% else %}text-slate-600 hover:bg-slate-100{% endif %}">15d</a>
      <a href="?period=30d" class="px-3 py-1.5 rounded-xl {% if period == '30d' %}bg-purple-600 text-white{% else %}text-slate-600 hover:bg-slate-100{% endif %}">30d</a>
    </div>
  </div>

  <!-- KPI Grid -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm">
      <div class="text-[10px] font-bold text-slate-400 uppercase">Period Revenue</div>
      <div class="text-xl font-black text-emerald-600 mt-1">৳ {{ paid_rev }}</div>
    </div>
    <div class="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm">
      <div class="text-[10px] font-bold text-slate-400 uppercase">Avg. Order Value</div>
      <div class="text-xl font-black text-slate-800 mt-1">৳ {{ avg_paid_order }}</div>
    </div>
    <div class="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm">
      <div class="text-[10px] font-bold text-slate-400 uppercase">Conversion Rate</div>
      <div class="text-xl font-black text-purple-600 mt-1">{{ visitor_to_purchase_rate }}%</div>
    </div>
    <div class="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm">
      <div class="text-[10px] font-bold text-slate-400 uppercase">Cart Abandonment</div>
      <div class="text-xl font-black text-rose-500 mt-1">{{ abandoned_carts }}</div>
    </div>
  </div>

  <!-- Charts Row 1: Revenue Trend & Traffic -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-3">
      <h3 class="text-xs font-bold uppercase text-slate-500">Revenue Trend (Delivered Sales)</h3>
      <div class="h-64"><canvas id="revChart"></canvas></div>
    </div>
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-3">
      <h3 class="text-xs font-bold uppercase text-slate-500">Unique Visitors Traffic</h3>
      <div class="h-64"><canvas id="trafficChart"></canvas></div>
    </div>
  </div>

  <!-- Charts Row 2: Sales Funnel & Order Status Breakdown -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-3">
      <h3 class="text-xs font-bold uppercase text-slate-500">Store Sales Funnel</h3>
      <div class="h-64"><canvas id="funnelChart"></canvas></div>
    </div>
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-3">
      <h3 class="text-xs font-bold uppercase text-slate-500">Orders Status Distribution</h3>
      <div class="h-64"><canvas id="statusChart"></canvas></div>
    </div>
  </div>

  <!-- Charts Row 3: Device Analytics & Top Selling Products -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-3">
      <h3 class="text-xs font-bold uppercase text-slate-500">Device Platform Breakdown</h3>
      <div class="h-64"><canvas id="deviceChart"></canvas></div>
    </div>
    <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-3">
      <h3 class="text-xs font-bold uppercase text-slate-500">Top Ordered Products</h3>
      <div class="h-64"><canvas id="topOrderChart"></canvas></div>
    </div>
  </div>
</div>

<script>
  // 1. Revenue
  new Chart(document.getElementById('revChart'), {
    type: 'line',
    data: {
      labels: {{ rev_labels|safe }},
      datasets: [{ label: 'Sales (BDT)', data: {{ rev_data|safe }}, borderColor: '#059669', backgroundColor: 'rgba(5, 150, 105, 0.1)', fill: true, tension: 0.3 }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });

  // 2. Traffic
  new Chart(document.getElementById('trafficChart'), {
    type: 'bar',
    data: {
      labels: {{ chart_labels|safe }},
      datasets: [{ label: 'Visitors', data: {{ chart_data|safe }}, backgroundColor: '#7C3AED', borderRadius: 6 }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });

  // 3. Funnel
  new Chart(document.getElementById('funnelChart'), {
    type: 'bar',
    data: {
      labels: {{ funnel_labels|safe }},
      datasets: [{ label: 'Users', data: {{ funnel_data|safe }}, backgroundColor: ['#3B82F6', '#8B5CF6', '#EC4899', '#F97316', '#10B981'], borderRadius: 6 }]
    },
    options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y' }
  });

  // 4. Status
  new Chart(document.getElementById('statusChart'), {
    type: 'doughnut',
    data: {
      labels: {{ status_labels|safe }},
      datasets: [{ data: {{ status_data|safe }}, backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#6B7280'] }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });

  // 5. Device
  new Chart(document.getElementById('deviceChart'), {
    type: 'pie',
    data: {
      labels: {{ device_labels|safe }},
      datasets: [{ data: {{ device_data|safe }}, backgroundColor: ['#6366F1', '#EC4899', '#14B8A6'] }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });

  // 6. Top Ordered
  new Chart(document.getElementById('topOrderChart'), {
    type: 'bar',
    data: {
      labels: {{ order_labels|safe }},
      datasets: [{ label: 'Units Sold', data: {{ order_data|safe }}, backgroundColor: '#5C3214', borderRadius: 6 }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
</script>
{% endblock %}
"""

# -------------------------------------------------------------
# 6. STOREFRONT TEMPLATES
# -------------------------------------------------------------
FILES["templates/index.html"] = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ site_setting.site_name }} - Premium Mobile Covers & Accessories</title>
  <meta name="description" content="Shop premium mobile cases, key rings and luxury accessories online in Bangladesh with fast Cash on Delivery!">
  <meta property="og:title" content="{{ site_setting.site_name }}">
  <meta property="og:description" content="Premium phone accessories with cash on delivery across Bangladesh.">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    .cart-drawer { transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
    .cart-hidden { transform: translateX(100%); }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .animate-marquee { display: inline-block; white-space: nowrap; animation: marquee 25s linear infinite; }
  </style>
</head>
<body class="bg-[#FAF9F5] text-slate-900 flex flex-col min-h-screen">

  <!-- Top Helpline & WhatsApp Bar -->
  <div class="bg-white border-b border-slate-100 text-xs py-2 px-4 sm:px-8">
    <div class="max-w-7xl mx-auto flex justify-between items-center text-slate-600">
      <div class="flex items-center gap-4">
        <span><i class="fa-solid fa-phone text-amber-900 mr-1"></i> Helpline: <strong>{{ site_setting.contact_phone }}</strong></span>
        {% if site_setting.whatsapp_number %}
        <a href="https://wa.me/{{ site_setting.whatsapp_number }}" target="_blank" class="text-emerald-600 font-bold hover:underline flex items-center gap-1">
          <i class="fa-brands fa-whatsapp text-sm"></i> WhatsApp ({{ site_setting.whatsapp_username|default:site_setting.whatsapp_number }})
        </a>
        {% endif %}
      </div>
      <div class="hidden sm:flex items-center gap-5 text-[11px] text-slate-500 font-medium">
        <span><i class="fa-solid fa-shield-halved text-emerald-600"></i> 100% Quality Verified</span>
        <span><i class="fa-solid fa-truck-fast text-purple-600"></i> Cash on Delivery in Bangladesh</span>
      </div>
    </div>
  </div>

  <!-- Header -->
  <header class="bg-white sticky top-0 z-40 border-b border-slate-200 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 h-20 flex items-center justify-between gap-4">
      <a href="/" class="flex items-center gap-1.5">
        <span class="text-2xl sm:text-3xl font-black italic tracking-tighter text-slate-900 uppercase">
          {{ site_setting.site_name }}<span class="text-xs not-italic font-bold align-super text-amber-900">™</span>
        </span>
      </a>

      <!-- Search Bar -->
      <div class="flex-1 max-w-xl mx-2">
        <div class="relative flex items-center">
          <input type="text" id="storeSearch" oninput="searchLive(this.value)" placeholder="Search phone covers, key rings..." class="w-full h-11 pl-11 pr-4 rounded-full border border-slate-300 text-xs focus:outline-none focus:border-slate-900 bg-slate-50">
          <i class="fa-solid fa-magnifying-glass absolute left-4 text-slate-400 text-xs"></i>
        </div>
      </div>

      <!-- Bag Button -->
      <button onclick="toggleCart()" class="relative w-11 h-11 rounded-full border border-slate-200 bg-slate-50 flex items-center justify-center text-slate-800 hover:bg-slate-100 transition shadow-sm">
        <i class="fa-solid fa-bag-shopping text-sm"></i>
        <span id="cartCountBadge" class="absolute -top-1 -right-1 bg-slate-900 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center font-bold">0</span>
      </button>
    </div>

    <!-- Category Strip -->
    <div class="bg-white border-t border-slate-100 px-4 sm:px-6">
      <div class="max-w-7xl mx-auto flex items-center gap-3 py-2 overflow-x-auto text-xs font-bold whitespace-nowrap">
        <a href="#all-products-section" class="bg-amber-100/70 text-amber-900 px-3.5 py-1.5 rounded-xl shrink-0">ALL PRODUCTS</a>
        {% for cat in categories %}
        <a href="{% url 'shop_category' cat.slug %}" class="px-3 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition shrink-0">
          {{ cat.name }}
        </a>
        {% endfor %}
      </div>
    </div>
  </header>

  <!-- Modern Accessible Announcement Ticker (Pure CSS) -->
  {% if site_setting.announcement_notice %}
  <div class="bg-white border-b border-slate-200 py-2 overflow-hidden relative">
    <div class="max-w-7xl mx-auto px-4 flex items-center gap-3 text-xs font-semibold text-slate-700">
      <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping shrink-0"></span>
      <div class="overflow-hidden w-full">
        <span class="animate-marquee">📢 {{ site_setting.announcement_notice }}</span>
      </div>
    </div>
  </div>
  {% endif %}

  <main class="flex-1">
    <!-- Categories Squircle Cards -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-4">
        {% for cat in categories %}
        <a href="{% url 'shop_category' cat.slug %}" class="group bg-white rounded-3xl p-4 border border-slate-100 hover:shadow-lg transition flex flex-col items-center text-center">
          <div class="w-16 h-16 rounded-2xl bg-slate-50 flex items-center justify-center overflow-hidden mb-3 group-hover:scale-105 transition">
            {% if cat.image %}
              <img src="{{ cat.image.url }}" alt="{{ cat.name }}" class="w-full h-full object-cover">
            {% else %}
              <i class="fa-solid fa-shapes text-2xl text-slate-400"></i>
            {% endif %}
          </div>
          <span class="text-xs font-bold text-slate-800">{{ cat.name }}</span>
        </a>
        {% endfor %}
      </div>
    </section>

    <!-- Dynamic Showcase Sections (Flash Sale with REAL working Countdown) -->
    {% for section in showcase_sections %}
    <section class="py-10 {% if section.background_style == 'brown' %}bg-[#5C3214] text-white{% elif section.background_style == 'dark' %}bg-slate-900 text-white{% else %}bg-transparent text-slate-900{% endif %}">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex justify-between items-center mb-8">
          <h2 class="text-2xl sm:text-3xl font-black tracking-tight">{{ section.title }}</h2>
          {% if section.has_countdown and section.end_time %}
          <div class="flex items-center gap-1.5 text-xs font-mono font-bold countdown-timer" data-endtime="{{ section.end_time|date:'c' }}">
            <span class="bg-black/30 backdrop-blur px-2.5 py-1.5 rounded-lg cd-h">00</span> :
            <span class="bg-black/30 backdrop-blur px-2.5 py-1.5 rounded-lg cd-m">00</span> :
            <span class="bg-black/30 backdrop-blur px-2.5 py-1.5 rounded-lg cd-s">00</span>
          </div>
          {% endif %}
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-5">
          {% for product in section.products.all %}
          <div class="bg-white rounded-3xl p-4 border border-slate-100 hover:shadow-xl transition flex flex-col justify-between group text-slate-900">
            <div>
              <div class="flex justify-between items-start mb-2">
                {% if product.discount_percent > 0 %}
                <span class="bg-rose-500 text-white text-[10px] font-black px-2 py-0.5 rounded-full">
                  {{ product.discount_percent }}% OFF
                </span>
                {% else %}<span></span>{% endif %}
                {% if product.badge_tag %}
                <span class="bg-amber-50 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded-full">🔥 {{ product.badge_tag }}</span>
                {% endif %}
              </div>

              <a href="{% url 'product_detail' product.pk %}" class="aspect-square rounded-2xl bg-slate-50 overflow-hidden mb-3 flex items-center justify-center p-2 block">
                {% if product.image %}
                <img src="{{ product.image.url }}" alt="{{ product.name }}" class="w-full h-full object-contain group-hover:scale-105 transition">
                {% else %}
                <i class="fa-solid fa-box text-slate-300 text-3xl"></i>
                {% endif %}
              </a>

              <a href="{% url 'product_detail' product.pk %}" class="font-bold text-xs text-slate-800 line-clamp-1 hover:text-amber-900 block">
                {{ product.name }}
              </a>
              <div class="text-[11px] font-semibold text-emerald-600 mt-1">● In Stock ({{ product.stock }})</div>
            </div>

            <div class="mt-4">
              <div class="flex items-center gap-2 mb-3">
                <span class="text-base font-black text-slate-900">৳ {{ product.effective_price }}</span>
                {% if product.discount_price and product.discount_price < product.price %}
                <span class="text-xs text-slate-400 line-through">৳ {{ product.price }}</span>
                {% endif %}
              </div>
              <div class="flex items-center gap-2">
                <button onclick="addToBag('{{ product.id }}', '{{ product.name|escapejs }}', '{{ product.effective_price }}', '{% if product.image %}{{ product.image.url }}{% endif %}')" class="flex-1 bg-slate-900 hover:bg-black text-white py-2 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-sm">
                  <i class="fa-solid fa-basket-shopping"></i> Add to Bag
                </button>
              </div>
            </div>
          </div>
          {% endfor %}
        </div>
      </div>
    </section>
    {% endfor %}

    <!-- All Products Catalog -->
    <section id="all-products-section" class="py-14 bg-white border-t border-slate-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex justify-between items-center mb-10 pb-4 border-b border-slate-100">
          <div>
            <span class="text-xs font-bold uppercase tracking-wider text-amber-900 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">Complete Catalog</span>
            <h2 class="text-3xl font-black text-slate-900 tracking-tight mt-2">All Products</h2>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {% for product in products %}
          <div class="bg-white rounded-3xl p-4 border border-slate-100 hover:shadow-xl transition flex flex-col justify-between group">
            <div>
              <div class="flex justify-between items-start mb-2">
                {% if product.discount_percent > 0 %}
                <span class="bg-rose-500 text-white text-[10px] font-black px-2 py-0.5 rounded-full">{{ product.discount_percent }}% OFF</span>
                {% else %}<span></span>{% endif %}
              </div>
              <a href="{% url 'product_detail' product.pk %}" class="aspect-square rounded-2xl bg-slate-50 overflow-hidden mb-3 flex items-center justify-center p-2 block">
                {% if product.image %}<img src="{{ product.image.url }}" alt="{{ product.name }}" class="w-full h-full object-contain group-hover:scale-105 transition">{% endif %}
              </a>
              <a href="{% url 'product_detail' product.pk %}" class="font-bold text-xs text-slate-800 line-clamp-1 block">{{ product.name }}</a>
              <div class="text-[11px] font-semibold text-emerald-600 mt-1">● In Stock</div>
            </div>
            <div class="mt-4">
              <div class="flex items-center gap-2 mb-3">
                <span class="text-base font-black text-slate-900">৳ {{ product.effective_price }}</span>
                {% if product.discount_price and product.discount_price < product.price %}
                <span class="text-xs text-slate-400 line-through">৳ {{ product.price }}</span>
                {% endif %}
              </div>
              <button onclick="addToBag('{{ product.id }}', '{{ product.name|escapejs }}', '{{ product.effective_price }}', '{% if product.image %}{{ product.image.url }}{% endif %}')" class="w-full bg-slate-900 hover:bg-black text-white py-2.5 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5">
                <i class="fa-solid fa-basket-shopping"></i> Add to Bag
              </button>
            </div>
          </div>
          {% endfor %}
        </div>
      </div>
    </section>
  </main>

  <!-- Cart Drawer -->
  <div id="cartDrawer" class="fixed inset-y-0 right-0 w-full max-w-md bg-white shadow-2xl z-50 cart-drawer cart-hidden flex flex-col">
    <div class="p-5 border-b border-slate-100 flex justify-between items-center bg-[#FAF9F5]">
      <div class="flex items-center gap-2">
        <i class="fa-solid fa-bag-shopping text-amber-900"></i>
        <h2 class="text-base font-bold text-slate-900">Your Shopping Bag</h2>
      </div>
      <button onclick="toggleCart()" class="text-slate-400 hover:text-black text-xl p-1">&times;</button>
    </div>
    <div id="cartItemsContainer" class="flex-1 p-5 overflow-y-auto space-y-3"></div>
    <div class="p-5 border-t border-slate-100 bg-[#FAF9F5] space-y-3">
      <div class="flex justify-between items-center text-sm font-bold">
        <span>Items Subtotal</span><span id="cartTotalPrice">৳ 0</span>
      </div>
      <button onclick="openCheckoutModal()" class="w-full bg-[#5C3214] text-white py-3.5 rounded-2xl font-bold text-xs shadow-lg hover:opacity-95 transition">
        Proceed to Checkout &rarr;
      </button>
    </div>
  </div>
  <div id="cartBackdrop" class="hidden fixed inset-0 bg-slate-900/60 z-40 transition-opacity" onclick="toggleCart()"></div>

  <!-- Cash on Delivery Checkout Modal with Promo Code Breakdown -->
  <div id="checkoutModal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl w-full max-w-lg p-6 sm:p-8 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-center border-b pb-3">
        <h3 class="font-bold text-slate-900 text-base">Cash on Delivery Order</h3>
        <button onclick="closeCheckoutModal()" class="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
      </div>

      <form id="checkoutForm" onsubmit="handlePlaceOrder(event)" class="space-y-3">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Full Name *</label>
          <input type="text" id="co_name" required placeholder="e.g. Mosabbir Ahmad" class="w-full border rounded-xl px-4 py-2 text-xs bg-slate-50 outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Mobile Number *</label>
          <input type="text" id="co_phone" required placeholder="017xxxxxxxx" class="w-full border rounded-xl px-4 py-2 text-xs bg-slate-50 outline-none">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">District *</label>
            <select id="co_district" required onchange="handleDistrictChange(this.value)" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
              <option value="Dhaka" selected>Dhaka</option>
              <option value="Chittagong">Chittagong</option>
              <option value="Sylhet">Sylhet</option>
              <option value="Rajshahi">Rajshahi</option>
              <option value="Khulna">Khulna</option>
              <option value="Barisal">Barisal</option>
              <option value="Rangpur">Rangpur</option>
              <option value="Gazipur">Gazipur</option>
              <option value="Other">Other Location</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Thana / Area</label>
            <input type="text" id="co_thana" placeholder="e.g. Mirpur, Dhanmondi" class="w-full border rounded-xl px-3 py-2 text-xs bg-slate-50 outline-none">
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Full Street Address *</label>
          <textarea id="co_address" required rows="2" placeholder="House, Road, Area, Landmark" class="w-full border rounded-xl p-3 text-xs bg-slate-50 outline-none"></textarea>
        </div>

        <!-- Working Promo Code Input -->
        <div class="flex gap-2 pt-1">
          <input type="text" id="promoInput" placeholder="Coupon Code (e.g. SAVE10)" class="flex-1 border rounded-xl px-3 py-2 text-xs uppercase font-mono bg-slate-50 outline-none">
          <button type="button" onclick="applyPromoCode()" class="bg-slate-900 text-white px-4 py-2 rounded-xl text-xs font-bold hover:bg-black">Apply</button>
        </div>
        <div id="promoMsg" class="text-[11px] font-bold"></div>

        <div class="p-4 bg-amber-50/70 border border-amber-200/60 rounded-2xl text-xs space-y-1.5 font-semibold text-slate-800">
          <div class="flex justify-between"><span>Items Subtotal:</span><span id="summary_prod_price">৳ 0</span></div>
          <div class="flex justify-between text-emerald-700"><span>Coupon Discount:</span><span id="summary_discount">- ৳ 0</span></div>
          <div class="flex justify-between"><span>Delivery Fee:</span><span id="summary_del_charge">৳ 70</span></div>
          <div class="border-t border-amber-200 pt-1.5 flex justify-between text-sm font-black text-amber-900">
            <span>Total Payable:</span><span id="summary_total_bill">৳ 0</span>
          </div>
        </div>

        <button type="submit" id="submitOrderBtn" class="w-full py-3.5 bg-[#5C3214] text-white rounded-2xl font-bold text-xs hover:opacity-95 transition shadow-lg">
          Confirm Order (Cash on Delivery)
        </button>
      </form>
    </div>
  </div>

  <!-- Footer -->
  <footer class="bg-slate-950 text-slate-400 text-xs py-10 mt-16 border-t border-slate-800 text-center space-y-2">
    <p class="font-black text-white text-lg tracking-wider uppercase">{{ site_setting.site_name }}</p>
    <p>{{ site_setting.office_address }} | Helpline: {{ site_setting.contact_phone }}</p>
    <p class="text-slate-600">&copy; 2026 {{ site_setting.site_name }}. All Rights Reserved.</p>
  </footer>

  <script>
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    let cart = JSON.parse(localStorage.getItem('fantacy_cart') || '[]');
    let currentDiscount = 0;
    let appliedPromoCode = '';
    const feeDhaka = parseFloat("{{ site_setting.delivery_fee_dhaka|default:70 }}");
    const feeOutside = parseFloat("{{ site_setting.delivery_fee_outside|default:130 }}");
    let deliveryFee = feeDhaka;

    function saveCart() {
      localStorage.setItem('fantacy_cart', JSON.stringify(cart));
      renderCartUI();
    }
    function toggleCart() {
      document.getElementById('cartDrawer').classList.toggle('cart-hidden');
      document.getElementById('cartBackdrop').classList.toggle('hidden');
    }
    function addToBag(id, name, price, img) {
      const existing = cart.find(i => i.id === id);
      if (existing) { existing.qty += 1; }
      else { cart.push({ id, name, price: parseFloat(price), img: img || '', qty: 1 }); }
      saveCart();
      toggleCart();

      fetch('/api/log-event/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({ event_type: 'add_to_cart', product_id: id })
      });
    }
    function updateQty(idx, delta) {
      if (cart[idx]) {
        cart[idx].qty += delta;
        if (cart[idx].qty <= 0) cart.splice(idx, 1);
        saveCart();
      }
    }
    function removeCartItem(idx) {
      cart.splice(idx, 1);
      saveCart();
    }
    function renderCartUI() {
      document.getElementById('cartCountBadge').innerText = cart.reduce((a, b) => a + b.qty, 0);
      const container = document.getElementById('cartItemsContainer');
      const totalSpan = document.getElementById('cartTotalPrice');

      if (cart.length === 0) {
        container.innerHTML = `<div class="text-center py-16 text-slate-400 text-xs">Your shopping bag is empty</div>`;
        totalSpan.innerText = '৳ 0';
        return;
      }
      let total = 0, html = '';
      cart.forEach((item, idx) => {
        total += (item.price * item.qty);
        html += `
          <div class="flex items-center justify-between p-3 bg-white rounded-2xl border border-slate-100 shadow-sm">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-slate-50 border overflow-hidden shrink-0 flex items-center justify-center">
                ${item.img ? `<img src="${item.img}" class="w-full h-full object-cover">` : `<i class="fa-solid fa-box text-slate-300"></i>`}
              </div>
              <div>
                <h4 class="text-xs font-bold text-slate-800 line-clamp-1">${item.name}</h4>
                <div class="text-xs font-black text-slate-900 mt-0.5">৳ ${item.price}</div>
                <div class="flex items-center gap-2 mt-1">
                  <button onclick="updateQty(${idx}, -1)" class="w-5 h-5 rounded bg-slate-100 text-xs font-bold">-</button>
                  <span class="text-xs font-bold">${item.qty}</span>
                  <button onclick="updateQty(${idx}, 1)" class="w-5 h-5 rounded bg-slate-100 text-xs font-bold">+</button>
                </div>
              </div>
            </div>
            <button onclick="removeCartItem(${idx})" class="text-slate-400 hover:text-rose-500 p-2"><i class="fa-regular fa-trash-can"></i></button>
          </div>
        `;
      });
      container.innerHTML = html;
      totalSpan.innerText = `৳ ${total}`;
    }
    function handleDistrictChange(dist) {
      deliveryFee = (dist.toLowerCase() === 'dhaka') ? feeDhaka : feeOutside;
      updateBillSummary();
    }
    function updateBillSummary() {
      const prodTotal = cart.reduce((a, b) => a + (b.price * b.qty), 0);
      document.getElementById('summary_prod_price').innerText = `৳ ${prodTotal}`;
      document.getElementById('summary_discount').innerText = `- ৳ ${currentDiscount}`;
      document.getElementById('summary_del_charge').innerText = `৳ ${deliveryFee}`;
      document.getElementById('summary_total_bill').innerText = `৳ ${Math.max(0, prodTotal - currentDiscount) + deliveryFee}`;
    }
    function openCheckoutModal() {
      if (cart.length === 0) { alert('Your bag is empty!'); return; }
      updateBillSummary();
      document.getElementById('checkoutModal').classList.remove('hidden');
      fetch('/api/log-event/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({ event_type: 'checkout_start' })
      });
    }
    function closeCheckoutModal() {
      document.getElementById('checkoutModal').classList.add('hidden');
    }
    async function applyPromoCode() {
      const code = document.getElementById('promoInput').value.trim();
      const subtotal = cart.reduce((a, b) => a + (b.price * b.qty), 0);
      const msg = document.getElementById('promoMsg');
      if (!code) return;

      try {
        const res = await fetch('/api/apply-promo/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
          body: JSON.stringify({ code, subtotal })
        });
        const result = await res.json();
        if (result.status === 'success') {
          currentDiscount = result.discount;
          appliedPromoCode = result.code;
          msg.className = "text-[11px] font-bold text-emerald-600";
          msg.innerText = `Coupon Applied: ৳${result.discount} Discount!`;
          updateBillSummary();
        } else {
          msg.className = "text-[11px] font-bold text-rose-500";
          msg.innerText = result.message;
        }
      } catch (err) {
        msg.innerText = "Error applying coupon";
      }
    }
    async function handlePlaceOrder(e) {
      e.preventDefault();
      const btn = document.getElementById('submitOrderBtn');
      btn.disabled = true;
      btn.innerText = "Placing Order...";

      const payload = {
        name: document.getElementById('co_name').value,
        phone: document.getElementById('co_phone').value,
        district: document.getElementById('co_district').value,
        thana: document.getElementById('co_thana').value,
        address: document.getElementById('co_address').value,
        promo_code: appliedPromoCode,
        items: cart
      };

      try {
        const res = await fetch('/api/checkout/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
          body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (result.status === 'success') {
          alert(`🎉 Order Placed Successfully!\\nOrder ID: ${result.order_id}\\nTotal Bill: ৳ ${result.total}`);
          cart = [];
          saveCart();
          closeCheckoutModal();
          toggleCart();
        } else {
          alert('Error: ' + result.message);
        }
      } catch (err) {
        alert('Server communication error. Please try again.');
      } finally {
        btn.disabled = false;
        btn.innerText = "Confirm Order (Cash on Delivery)";
      }
    }

    // Working Flash Sale Countdown Engine
    setInterval(() => {
      document.querySelectorAll('.countdown-timer').forEach(el => {
        const endTime = new Date(el.dataset.endtime).getTime();
        const now = new Date().getTime();
        const diff = endTime - now;
        if (diff > 0) {
          const h = Math.floor(diff / (1000 * 60 * 60));
          const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          const s = Math.floor((diff % (1000 * 60)) / 1000);
          el.querySelector('.cd-h').innerText = String(h).padStart(2, '0');
          el.querySelector('.cd-m').innerText = String(m).padStart(2, '0');
          el.querySelector('.cd-s').innerText = String(s).padStart(2, '0');
        }
      });
    }, 1000);

    let searchTimer = null;
    function searchLive(val) {
      clearTimeout(searchTimer);
      if (val.trim().length > 1) {
        searchTimer = setTimeout(() => {
          fetch('/api/log-event/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
            body: JSON.stringify({ event_type: 'search', query: val.trim() })
          });
        }, 800);
      }
    }
    document.addEventListener('DOMContentLoaded', renderCartUI);
  </script>
</body>
</html>
"""

FILES["templates/shop/category_products.html"] = """{% extends 'index.html' %}
{% block content %}
<div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
  <div class="mb-8">
    <a href="/" class="text-xs font-bold text-amber-900">&larr; Back to Home</a>
    <h1 class="text-3xl font-black text-slate-900 mt-2">{{ category.name }}</h1>
    {% if category.short_description %}
    <p class="text-xs text-slate-500 mt-1">{{ category.short_description }}</p>
    {% endif %}
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
    {% for product in products %}
    <div class="bg-white rounded-3xl p-4 border border-slate-100 hover:shadow-xl transition flex flex-col justify-between">
      <div>
        <a href="{% url 'product_detail' product.pk %}" class="aspect-square rounded-2xl bg-slate-50 overflow-hidden mb-3 flex items-center justify-center p-2 block">
          {% if product.image %}<img src="{{ product.image.url }}" class="w-full h-full object-contain">{% endif %}
        </a>
        <a href="{% url 'product_detail' product.pk %}" class="font-bold text-xs text-slate-800 line-clamp-1 block">{{ product.name }}</a>
      </div>
      <div class="mt-4">
        <div class="font-black text-slate-900 mb-3">৳ {{ product.effective_price }}</div>
        <button onclick="addToBag('{{ product.id }}', '{{ product.name|escapejs }}', '{{ product.effective_price }}', '{% if product.image %}{{ product.image.url }}{% endif %}')" class="w-full bg-slate-900 hover:bg-black text-white py-2 rounded-xl text-xs font-bold">
          Add to Bag
        </button>
      </div>
    </div>
    {% empty %}
    <div class="col-span-full text-center py-20 text-slate-400">No products found in this category yet.</div>
    {% endfor %}
  </div>
</div>
{% endblock %}
"""

FILES["templates/shop/product_detail.html"] = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ product.name }} - {{ site_setting.site_name }}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>body { font-family: 'Plus Jakarta Sans', sans-serif; }</style>
</head>
<body class="bg-[#FAF9F5] text-slate-900 flex flex-col min-h-screen">
  <header class="bg-white border-b border-slate-200 h-20 flex items-center justify-between px-6">
    <a href="/" class="text-2xl font-black italic text-slate-900 uppercase">{{ site_setting.site_name }}</a>
    <a href="/" class="text-xs font-bold text-slate-600 hover:text-black">&larr; Continue Shopping</a>
  </header>

  <main class="max-w-6xl mx-auto px-4 sm:px-6 py-10 flex-1">
    <div class="bg-white rounded-3xl p-6 sm:p-10 border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-2 gap-10">
      <div>
        <div class="aspect-square bg-slate-50 rounded-2xl overflow-hidden border flex items-center justify-center p-4">
          <img id="mainImg" src="{% if product.image %}{{ product.image.url }}{% endif %}" class="max-h-full max-w-full object-contain">
        </div>
      </div>
      <div class="space-y-4 flex flex-col justify-between">
        <div class="space-y-3">
          {% if product.badge_tag %}
          <span class="inline-block bg-amber-50 text-amber-800 text-xs font-bold px-3 py-1 rounded-full border border-amber-200">🔥 {{ product.badge_tag }}</span>
          {% endif %}
          <h1 class="text-2xl sm:text-3xl font-black text-slate-900">{{ product.name }}</h1>
          <div class="text-xs font-semibold text-emerald-600">● In Stock ({{ product.stock }} units available)</div>
          <div class="text-3xl font-black text-slate-900">৳ {{ product.effective_price }}</div>
          <p class="text-xs text-slate-600 leading-relaxed">{{ product.description|default:"Crafted with highest quality materials." }}</p>
        </div>
        <div class="pt-4 border-t">
          <a href="/" class="block text-center w-full py-3.5 bg-slate-900 text-white rounded-2xl font-bold text-xs hover:bg-black transition shadow-lg">
            Add via Storefront Bag
          </a>
        </div>
      </div>
    </div>
  </main>
</body>
</html>
"""

# -------------------------------------------------------------
# 7. WRITE ALL FILES TO DISK
# -------------------------------------------------------------
for filepath, content in FILES.items():
    folder = os.path.dirname(filepath)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"  [+] Created: {filepath}")

# -------------------------------------------------------------
# 8. CLEANUP OF CORRUPTED / OBSOLETE FILES
# -------------------------------------------------------------
corrupted_files = [
    "templates/admin_custom/categories.html`",
    "templates/merchant/promo.html`",
    "templates/admin_custom/dashboard.html",
    "templates/admin_custom/products.html",
    "templates/admin_custom/orders.html",
    "templates/admin_custom/customers.html",
    "templates/admin_custom/analytics.html",
    "templates/admin_custom/categories.html",
    "templates/admin_custom/promo.html",
    "templates/admin_custom/edit_product.html",
    "templates/admin_custom/edit_category.html",
    "templates/admin_custom/base.html",
]

for cf in corrupted_files:
    if os.path.exists(cf):
        try:
            os.remove(cf)
            print(f"  [-] Removed dead/corrupted file: {cf}")
        except Exception:
            pass

print("=" * 60)
print("✅ সফল! আপনার প্রোজেক্টের সমস্ত ফাইল তৈরি ও সাজানো সম্পন্ন হয়েছে।")
print("=" * 60)