from django.urls import path
from . import views

urlpatterns = [
    # Customer Shop Front
    path('', views.home_view, name='home'),
    path('category/<slug:slug>/', views.shop_category_view, name='shop_category'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),

    # Merchant Admin Authentication
    path('mosabbiradmin/login/', views.admin_login_view, name='admin_login'),
    path('mosabbiradmin/logout/', views.admin_logout_view, name='admin_logout'),

    # Merchant Admin Panel (Protected & Separate)
    path('mosabbiradmin/', views.merchant_dashboard, name='merchant_dashboard'),
    path('mosabbiradmin/orders/', views.merchant_orders, name='merchant_orders'),
    path('mosabbiradmin/orders/export/', views.export_orders_csv, name='export_orders_csv'),
    path('mosabbiradmin/orders/<int:pk>/update/', views.update_order_status, name='update_order_status'),
    path('mosabbiradmin/products/', views.merchant_products, name='merchant_products'),
    path('mosabbiradmin/products/<int:pk>/edit/', views.merchant_edit_product, name='merchant_edit_product'),
    path('mosabbiradmin/products/<int:pk>/delete/', views.merchant_delete_product, name='merchant_delete_product'),
    path('mosabbiradmin/add-product/', views.add_product, name='add_product'),
    path('mosabbiradmin/categories/', views.merchant_categories, name='merchant_categories'),
    path('mosabbiradmin/categories/<int:pk>/', views.merchant_category_detail, name='merchant_category_detail'),
    path('mosabbiradmin/categories/<int:pk>/toggle/', views.merchant_toggle_category, name='merchant_toggle_category'),
    path('mosabbiradmin/categories/<int:pk>/delete/', views.merchant_delete_category, name='merchant_delete_category'),
    path('mosabbiradmin/analytics/', views.merchant_analytics, name='merchant_analytics'),
    path('mosabbiradmin/promos/', views.merchant_promos, name='merchant_promos'),
    path('mosabbiradmin/promos/<int:pk>/toggle/', views.toggle_promo, name='toggle_promo'),
    path('mosabbiradmin/promos/<int:pk>/delete/', views.delete_promo, name='delete_promo'),
]
