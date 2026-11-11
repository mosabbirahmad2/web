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
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

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
            optimize_image(self.image, max_size=(600, 600))
        if self.banner:
            optimize_image(self.banner, max_size=(1400, 450))
        super().save(*args, **kwargs)
        cache.delete('global_active_categories')

    def delete(self, *args, **kwargs):
        if self.image:
            try:
                self.image.delete(save=False)
            except Exception:
                pass
        if self.banner:
            try:
                self.banner.delete(save=False)
            except Exception:
                pass
        super().delete(*args, **kwargs)
        cache.delete('global_active_categories')

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    product_code = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Unique Product Code / SKU")
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
        # Auto-generate unique product_code if not provided
        if not self.product_code:
            base_code = f"FT-{uuid.uuid4().hex[:6].upper()}"
            while Product.objects.filter(product_code=base_code).exclude(pk=self.pk).exists():
                base_code = f"FT-{uuid.uuid4().hex[:6].upper()}"
            self.product_code = base_code

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

    def delete(self, *args, **kwargs):
        # Delete associated gallery images
        for image in self.images.all():
            if image.image:
                try:
                    image.image.delete(save=False)
                except Exception:
                    pass
            image.delete(save=False)
        # Delete main image
        if self.image:
            try:
                self.image.delete(save=False)
            except Exception:
                pass
        super().delete(*args, **kwargs)

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
        return f"[{self.product_code or 'NO-CODE'}] {self.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image:
            optimize_image(self.image, max_size=(900, 900))
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image:
            try:
                self.image.delete(save=False)
            except Exception:
                pass
        super().delete(*args, **kwargs)


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
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum total usage limit")
    used_count = models.PositiveIntegerField(default=0, help_text="Number of times redeemed")
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self, subtotal=0):
        if not self.is_active:
            return False, "This promo code is currently disabled."
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False, "This promo code has expired."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "This promo code has reached its maximum usage limit."
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
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='Placed', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            while True:
                generated_id = f"FT-{uuid.uuid4().hex[:10].upper()}"
                if not Order.objects.filter(order_id=generated_id).exists():
                    self.order_id = generated_id
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
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES, default='visit', db_index=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']


class SearchQuery(models.Model):
    query = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


@receiver(pre_delete, sender=Product)
def auto_delete_product_files(sender, instance, **kwargs):
    # Delete associated gallery images
    for image in instance.images.all():
        if image.image:
            try:
                image.image.delete(save=False)
            except Exception:
                pass
        image.delete(save=False)
    # Delete main image file
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception:
            pass
    # Delete related analytics events
    instance.analyticsevent_set.all().delete()


@receiver(pre_save, sender=Product)
def auto_delete_old_product_image_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_file = Product.objects.get(pk=instance.pk).image
    except Product.DoesNotExist:
        return
    if old_file and old_file != instance.image:
        try:
            old_file.delete(save=False)
        except Exception:
            pass


@receiver(pre_delete, sender=ProductImage)
def auto_delete_product_image_file(sender, instance, **kwargs):
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception:
            pass


@receiver(pre_delete, sender=Category)
def auto_delete_category_files(sender, instance, **kwargs):
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception:
            pass
    if instance.banner:
        try:
            instance.banner.delete(save=False)
        except Exception:
            pass


@receiver(pre_save, sender=Category)
def auto_delete_old_category_files_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_cat = Category.objects.get(pk=instance.pk)
    except Category.DoesNotExist:
        return
    if old_cat.image and old_cat.image != instance.image:
        try:
            old_cat.image.delete(save=False)
        except Exception:
            pass
    if old_cat.banner and old_cat.banner != instance.banner:
        try:
            old_cat.banner.delete(save=False)
        except Exception:
            pass

