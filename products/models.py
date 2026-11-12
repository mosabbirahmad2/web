import os
import uuid
from io import BytesIO
from PIL import Image

from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.db.models import Avg

def optimize_image(image_field, max_size=(1000, 1000), quality=85):
    """Critical Bug Fix: Prevent double nested directory path on save"""
    if not image_field or not hasattr(image_field, 'file'):
        return
    try:
        img = Image.open(image_field)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        out = BytesIO()
        img.save(out, format='WEBP', quality=quality, optimize=True)
        out.seek(0)
        
        base_name = os.path.basename(image_field.name)
        clean_name = os.path.splitext(base_name)[0]
        image_field.file = ContentFile(out.read())
        image_field.name = f"{clean_name}.webp"
    except Exception:
        pass


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=100, default="Fantacy Tech")
    contact_phone = models.CharField(max_length=30, default="01999999999")
    whatsapp_number = models.CharField(max_length=30, default="01999999999")
    whatsapp_username = models.CharField(max_length=100, default="fantacytech", blank=True)
    contact_email = models.EmailField(default="support@fantacytech.com")
    office_address = models.TextField(default="Dhaka, Bangladesh")
    announcement_notice = models.CharField(max_length=300, default="Welcome to Fantacy Tech! Premium Phone Covers & Key Rings with Fast Home Delivery!")
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
        cache.delete('global_site_settings')

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
        return bool(self.locked_until and self.locked_until > timezone.now())


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    short_description = models.TextField(blank=True, null=True)
    banner = models.ImageField(upload_to='categories/banners/', blank=True, null=True)
    image = models.ImageField(upload_to='categories/images/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "cat"
            slug = base
            c = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{c}"
                c += 1
            self.slug = slug
        if self.image:
            optimize_image(self.image, max_size=(600, 600))
        if self.banner:
            optimize_image(self.banner, max_size=(1400, 450))
        super().save(*args, **kwargs)
        cache.delete('global_active_categories')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('global_active_categories')

    def __str__(self):
        return f"{self.parent.name} > {self.name}" if self.parent else self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    product_code = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Product Code / SKU")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=50)
    badge_tag = models.CharField(max_length=50, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.discount_price and self.discount_price > self.price:
            raise ValidationError({'discount_price': 'Discount price cannot exceed regular price.'})

    def save(self, *args, **kwargs):
        if not self.product_code:
            code = f"FT-{uuid.uuid4().hex[:6].upper()}"
            while Product.objects.filter(product_code=code).exclude(pk=self.pk).exists():
                code = f"FT-{uuid.uuid4().hex[:6].upper()}"
            self.product_code = code

        if self.discount_price and self.discount_price > self.price:
            self.discount_price = self.price
        if not self.slug:
            base = slugify(self.name) or "prod"
            slug = base
            c = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{c}"
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
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def avg_rating(self):
        avg = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 5.0

    @property
    def reviews_count(self):
        return self.reviews.filter(is_approved=True).count()

    def __str__(self):
        return f"[{self.product_code or 'NO-SKU'}] {self.name}"


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
        ('light', 'White / Minimal'),
        ('brown', 'Warm Coffee Brown'),
        ('dark', 'Charcoal Black'),
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    background_style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='light')
    has_countdown = models.BooleanField(default=False)
    end_time = models.DateTimeField(null=True, blank=True)
    products = models.ManyToManyField(Product, blank=True, related_name='showcases')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def is_expired(self):
        return bool(self.has_countdown and self.end_time and self.end_time <= timezone.now())

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "section"
            slug = base
            c = 1
            while ShowcaseSection.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{c}"
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
    discount_value = models.PositiveIntegerField(default=10)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self, subtotal=0):
        if not self.is_active:
            return False, "This promo code is disabled."
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False, "This promo code has expired."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "This promo code usage limit has been reached."
        if self.min_purchase and subtotal < self.min_purchase:
            return False, f"Minimum spend of ৳{self.min_purchase} required."
        return True, "Valid"

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percentage':
            d = (subtotal * self.discount_value) / 100
            if self.max_discount and d > self.max_discount:
                d = self.max_discount
        else:
            d = self.discount_value
        return min(d, subtotal)

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
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='Placed', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            while True:
                candidate = f"FT-{uuid.uuid4().hex[:10].upper()}"
                if not Order.objects.filter(order_id=candidate).exists():
                    self.order_id = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255, blank=True)
    product_code = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.product:
            if not self.product_name:
                self.product_name = self.product.name
            if not self.product_code and self.product.product_code:
                self.product_code = self.product.product_code
        super().save(*args, **kwargs)


class UniqueVisitorLog(models.Model):
    ip_address = models.GenericIPAddressField()
    session_key = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ip_address', 'date')
        ordering = ['-created_at']


class StoreVisitSession(models.Model):
    session_key = models.CharField(max_length=100, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


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
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES, default='visit', db_index=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)


class SearchQuery(models.Model):
    query = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
