from django.contrib import admin
from .models import Category, Product, ProductImage, ProductReview, Order, OrderItem, PromoCode, SiteSetting, StoreVisitSession

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'name', 'category', 'price', 'discount_price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'product_code', 'description')

admin.site.register(ProductImage)
admin.site.register(ProductReview)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(PromoCode)
admin.site.register(SiteSetting)
admin.site.register(StoreVisitSession)
