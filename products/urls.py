from django.urls import path
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
