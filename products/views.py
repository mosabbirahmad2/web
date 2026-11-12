import csv
import json
import os
from decimal import Decimal
from datetime import timedelta
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum, Q, Avg, F
from django.db.models.functions import TruncDate, TruncHour
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags, escape
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

# Rate Limiter
def rate_limit(requests_per_minute=60):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            ip = get_client_ip(request)
            cache_key = f"rl_{view_func.__name__}_{ip}"
            current_hits = cache.get(cache_key, 0)
            if current_hits >= requests_per_minute:
                return JsonResponse({'status': 'error', 'message': 'Too many requests. Please slow down.'}, status=429)
            cache.set(cache_key, current_hits + 1, timeout=60)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

# --- AUTHENTICATION ---
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
            messages.error(request, f"Security Alert: Locked out for {hours}h {mins}m.")
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
    showcase_sections = ShowcaseSection.objects.filter(is_active=True).prefetch_related('products__category')
    valid_sections = [s for s in showcase_sections if not s.is_expired()]

    search_query = request.GET.get('q', '').strip()
    products_list = Product.objects.filter(is_active=True).select_related('category').order_by('-created_at')

    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) | 
            Q(product_code__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    paginator = Paginator(products_list, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'index.html', {
        'categories': categories,
        'showcase_sections': valid_sections,
        'products': page_obj,
        'search_query': search_query,
    })

def shop_category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    sub_ids = category.subcategories.values_list('id', flat=True)
    products = Product.objects.filter(
        Q(category=category) | Q(category__id__in=sub_ids),
        is_active=True
    ).distinct().select_related('category').order_by('-created_at')

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'shop/category_products.html', {
        'category': category,
        'products': page_obj
    })

def product_detail_view(request, pk):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'reviews'), 
        pk=pk
    )
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
    name = escape(strip_tags(request.POST.get('name', 'Anonymous').strip()))[:100]
    rating = int(request.POST.get('rating', 5))
    if rating < 1 or rating > 5:
        rating = 5
    raw_comment = request.POST.get('comment', '').strip()
    comment = escape(strip_tags(raw_comment))

    if comment:
        ProductReview.objects.create(
            product=product, customer_name=name or 'Anonymous', rating=rating, comment=comment
        )
        messages.success(request, 'Thank you! Your review has been added.')
    return redirect('product_detail', pk=pk)

# --- SEARCH API WITH SKU MATCHING ---
@rate_limit(requests_per_minute=45)
def search_api(request):
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})

    try:
        SearchQuery.objects.create(query=q[:200], ip_address=get_client_ip(request))
    except Exception:
        pass

    matches = Product.objects.filter(
        Q(name__icontains=q) | Q(product_code__icontains=q) | Q(description__icontains=q),
        is_active=True
    ).select_related('category')[:8]

    data = []
    for p in matches:
        data.append({
            'id': p.id,
            'name': p.name,
            'code': p.product_code or '',
            'price': str(p.price),
            'discount_price': str(p.discount_price) if p.discount_price else None,
            'effective_price': str(p.effective_price),
            'discount_percent': p.discount_percent,
            'stock': p.stock,
            'image': p.image.url if p.image else None,
            'url': f'/product/{p.id}/'
        })

    return JsonResponse({'results': data})

# --- PROMO CODE VALIDATION API ---
@require_POST
@rate_limit(requests_per_minute=20)
def apply_promo_api(request):
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
        items = data.get('items', [])

        promo = PromoCode.objects.filter(code=code).first()
        if not promo:
            return JsonResponse({'status': 'error', 'message': 'Invalid promo code!'}, status=400)

        # Recalculate subtotal server-side using each product's effective_price
        calculated_subtotal = Decimal('0.00')
        if items and isinstance(items, list):
            for item in items:
                p_id = item.get('id')
                qty = int(item.get('qty', 1))
                if qty > 0:
                    prod = Product.objects.filter(id=p_id, is_active=True).first()
                    if prod:
                        calculated_subtotal += (prod.effective_price * qty)
        else:
            calculated_subtotal = Decimal(str(data.get('subtotal', 0)))

        is_valid, msg = promo.is_valid(subtotal=calculated_subtotal)
        if not is_valid:
            return JsonResponse({'status': 'error', 'message': msg}, status=400)

        discount = promo.calculate_discount(subtotal=calculated_subtotal)
        return JsonResponse({
            'status': 'success',
            'code': promo.code,
            'discount': float(discount),
            'new_total': float(max(Decimal('0.00'), calculated_subtotal - discount))
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@rate_limit(requests_per_minute=100)
def log_event_api(request):
    try:
        data = json.loads(request.body)
        event_type = data.get('event_type')
        product_id = data.get('product_id')
        query = data.get('query')

        if query:
            SearchQuery.objects.create(query=query.strip()[:200], ip_address=get_client_ip(request))

        product = Product.objects.filter(id=product_id).first() if product_id else None
        AnalyticsEvent.objects.create(
            ip_address=get_client_ip(request),
            path=request.path[:250],
            event_type=event_type,
            product=product
        )
        return JsonResponse({'status': 'ok'})
    except Exception:
        return JsonResponse({'status': 'ok'})

# --- CHECKOUT API (CLEANS INVALID ITEMS, ENFORCES EFFECTIVE_PRICE) ---
@require_POST
def place_order_api(request):
    ip = get_client_ip(request)
    cache_key = f"order_cooldown_{ip}"
    if cache.get(cache_key):
        return JsonResponse({'status': 'error', 'message': 'Please wait a moment before submitting again.'}, status=429)

    try:
        data = json.loads(request.body)
        name = escape(strip_tags(data.get('name', '').strip()))
        phone = escape(strip_tags(data.get('phone', '').strip()))
        district = escape(strip_tags(data.get('district', 'Dhaka').strip()))
        thana = escape(strip_tags(data.get('thana', '').strip()))
        address = escape(strip_tags(data.get('address', '').strip()))
        promo_code_str = data.get('promo_code', '').strip().upper()
        items = data.get('items', [])

        if not name or not phone or not address or not items:
            return JsonResponse({'status': 'error', 'message': 'Please fill out all required delivery fields!'}, status=400)

        setting = SiteSetting.get_settings()
        is_dhaka = (district.lower() == 'dhaka')
        delivery_fee = setting.delivery_fee_dhaka if is_dhaka else setting.delivery_fee_outside

        with transaction.atomic():
            subtotal = Decimal('0.00')
            validated_items = []
            invalid_product_names = []

            for item in items:
                prod_id = item.get('id')
                qty = int(item.get('qty', 1))
                if qty <= 0:
                    continue

                prod = Product.objects.select_for_update().filter(id=prod_id, is_active=True).first()
                if not prod:
                    invalid_product_names.append(str(prod_id))
                    continue

                if prod.stock < qty:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Insufficient stock for "{prod.name}". Only {prod.stock} unit(s) left.'
                    }, status=400)

                # ALWAYS USE EFFECTIVE PRICE (Discount price if available)
                item_price = prod.effective_price
                subtotal += (Decimal(str(item_price)) * qty)
                validated_items.append((prod, qty, item_price))

            # If cart only contained deleted/unavailable products
            if not validated_items:
                return JsonResponse({
                    'status': 'error',
                    'invalid_items': True,
                    'message': 'The items in your bag are no longer available. Your shopping bag has been cleared.'
                }, status=400)

            discount_amount = Decimal('0.00')
            applied_promo = None
            if promo_code_str:
                applied_promo = PromoCode.objects.select_for_update().filter(code=promo_code_str).first()
                if applied_promo:
                    valid, _ = applied_promo.is_valid(subtotal=subtotal)
                    if valid:
                        discount_amount = Decimal(str(applied_promo.calculate_discount(subtotal=subtotal)))
                    else:
                        applied_promo = None

            total_amount = max(Decimal('0.00'), subtotal - discount_amount) + Decimal(str(delivery_fee))

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

            for prod, qty, price in validated_items:
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    product_name=prod.name,
                    product_code=prod.product_code,
                    quantity=qty,
                    price=price
                )
                Product.objects.filter(id=prod.id).update(stock=F('stock') - qty)

            if applied_promo:
                PromoCode.objects.filter(id=applied_promo.id).update(used_count=F('used_count') + 1)

            AnalyticsEvent.objects.create(
                ip_address=ip,
                path='/checkout/success',
                event_type='order_completed'
            )

            cache.set(cache_key, True, timeout=5)

            return JsonResponse({
                'status': 'success',
                'order_id': order.order_id,
                'total': str(order.total_amount)
            })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# --- MERCHANT ADMIN ---
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
    orders = Order.objects.all().prefetch_related('items__product').order_by('-created_at')

    if status_filter and status_filter.lower() != 'all':
        orders = orders.filter(status__iexact=status_filter)
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) | 
            Q(customer_phone__icontains=search_query) | 
            Q(customer_name__icontains=search_query) | 
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
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Phone', 'District', 'Thana', 'Address', 'Fee', 'Discount', 'Total', 'Status', 'Date'])
    for o in Order.objects.all().order_by('-created_at'):
        writer.writerow([o.order_id, o.customer_name, o.customer_phone, o.district, o.thana or '', o.shipping_address, o.delivery_fee, o.discount_amount, o.total_amount, o.status, o.created_at.strftime('%Y-%m-%d %H:%M')])
    return response

# Customers Management with Order History
@login_required(login_url='admin_login')
def merchant_customers(request):
    search = request.GET.get('q', '').strip()
    customer_phone = request.GET.get('phone', '').strip()

    selected_customer_orders = None
    if customer_phone:
        selected_customer_orders = Order.objects.filter(customer_phone=customer_phone).prefetch_related('items').order_by('-created_at')

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
        'selected_customer_orders': selected_customer_orders,
        'selected_phone': customer_phone,
        'active_menu': 'customers',
        'search_query': search,
    })

# Products Management (Supports Up to 6 Images, SKU & Edit Modal)
@login_required(login_url='admin_login')
def merchant_products(request, edit_pk=None):
    search = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category', '').strip()
    products_qs = Product.objects.all().select_related('category').prefetch_related('images').order_by('-created_at')

    if search:
        products_qs = products_qs.filter(Q(name__icontains=search) | Q(product_code__icontains=search))
    if cat_id:
        products_qs = products_qs.filter(category_id=cat_id)

    edit_product = None
    if edit_pk:
        edit_product = get_object_or_404(Product, pk=edit_pk)

    paginator = Paginator(products_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    categories = Category.objects.all()

    return render(request, 'merchant/products.html', {
        'products': page_obj,
        'categories': categories,
        'edit_product': edit_product,
        'active_menu': 'products',
        'search_query': search,
        'selected_category': cat_id,
    })

@login_required(login_url='admin_login')
@require_POST
def add_product(request):
    name = request.POST.get('name', '').strip()
    product_code = request.POST.get('product_code', '').strip().upper() or None
    category_id = request.POST.get('category')
    description = request.POST.get('description', '').strip()
    price = request.POST.get('price')
    discount_price = request.POST.get('discount_price')
    stock = request.POST.get('stock', 50)
    badge_tag = request.POST.get('badge_tag', '').strip()
    is_featured = bool(request.POST.get('is_featured'))
    
    # 6 Images Support
    main_image = request.FILES.get('main_image')
    gallery_images = request.FILES.getlist('gallery_images')

    if name and category_id and price:
        category = get_object_or_404(Category, pk=category_id)
        d_price = Decimal(str(discount_price)) if discount_price else None
        r_price = Decimal(str(price))
        if d_price and d_price > r_price:
            d_price = r_price

        prod = Product.objects.create(
            name=name, product_code=product_code, category=category, description=description,
            price=r_price, discount_price=d_price, stock=int(stock),
            badge_tag=badge_tag, is_featured=is_featured, image=main_image
        )
        for g_img in gallery_images[:5]:
            ProductImage.objects.create(product=prod, image=g_img)

        messages.success(request, f'Product "{name}" (Code: {prod.product_code}) created successfully!')
    return redirect('merchant_products')

@login_required(login_url='admin_login')
def merchant_edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        p_code = request.POST.get('product_code', '').strip().upper()
        if p_code and not Product.objects.filter(product_code=p_code).exclude(pk=product.pk).exists():
            product.product_code = p_code

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

        # Handle additional gallery images (up to 5)
        new_gallery = request.FILES.getlist('gallery_images')
        for g_img in new_gallery:
            if product.images.count() < 5:
                ProductImage.objects.create(product=product, image=g_img)

        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('merchant_products')

    return merchant_products(request, edit_pk=pk)

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
def merchant_delete_product_image(request, pk):
    img = get_object_or_404(ProductImage, pk=pk)
    prod_pk = img.product.pk
    img.delete()
    messages.success(request, 'Gallery image removed.')
    return redirect('merchant_edit_product', pk=prod_pk)

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

# Categories & Sub-categories with Full Edit Support
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

        elif action == 'update_subcategory':
            sub_pk = request.POST.get('sub_pk')
            sub = get_object_or_404(Category, pk=sub_pk, parent=category)
            sub.name = request.POST.get('name', sub.name).strip()
            sub.short_description = request.POST.get('short_description', sub.short_description).strip()
            if 'banner' in request.FILES: sub.banner = request.FILES['banner']
            if 'image' in request.FILES: sub.image = request.FILES['image']
            sub.save()
            messages.success(request, f'Sub-category "{sub.name}" updated successfully!')
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

    total_sections = sections.count()
    active_sections = sections.filter(is_active=True).count()
    total_featured_products = sum(s.products.count() for s in sections)

    return render(request, 'merchant/sections.html', {
        'sections': sections,
        'all_products': all_products,
        'total_sections': total_sections,
        'active_sections': active_sections,
        'total_featured_products': total_featured_products,
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

# Settings & Theme Customizer
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

# ====================================================================
# EXECUTIVE E-COMMERCE BUSINESS ANALYTICS (CEO DASHBOARD)
# ====================================================================
@login_required(login_url='admin_login')
def merchant_analytics(request):
    period = request.GET.get('period', '30d').lower()
    now = timezone.now()

    if period == '24h':
        start_time = now - timedelta(hours=24)
        trunc_fn = TruncHour
        date_format = '%I %p'
    elif period == '7d':
        start_time = now - timedelta(days=7)
        trunc_fn = TruncDate
        date_format = '%b %d'
    elif period == 'all':
        start_time = now - timedelta(days=365)
        trunc_fn = TruncDate
        date_format = '%b %Y'
    else: # 30d default
        start_time = now - timedelta(days=30)
        trunc_fn = TruncDate
        date_format = '%b %d'

    # Orders Base Query
    period_orders = Order.objects.filter(created_at__gte=start_time)
    total_orders_count = period_orders.count()
    delivered_orders = period_orders.filter(status='Delivered')
    returned_orders = period_orders.filter(status='Returned')
    cancelled_orders = period_orders.filter(status='Cancelled')

    # Financial KPIs
    net_revenue = delivered_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    gross_pipeline = period_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    aov = delivered_orders.aggregate(Avg('total_amount'))['total_amount__avg'] or Decimal('0.00')

    # Operational Health KPIs
    return_rate = round((returned_orders.count() / total_orders_count * 100), 1) if total_orders_count > 0 else 0.0
    cancel_rate = round((cancelled_orders.count() / total_orders_count * 100), 1) if total_orders_count > 0 else 0.0
    delivery_success_rate = round((delivered_orders.count() / total_orders_count * 100), 1) if total_orders_count > 0 else 0.0

    # Traffic & Funnel
    unique_visitors = UniqueVisitorLog.objects.filter(created_at__gte=start_time).values('ip_address').distinct().count()
    product_views = AnalyticsEvent.objects.filter(event_type='product_view', timestamp__gte=start_time).count()
    add_to_cart_events = AnalyticsEvent.objects.filter(event_type='add_to_cart', timestamp__gte=start_time).count()
    checkout_starts = AnalyticsEvent.objects.filter(event_type='checkout_start', timestamp__gte=start_time).count()
    orders_completed = total_orders_count

    conversion_rate = round((orders_completed / unique_visitors * 100), 1) if unique_visitors > 0 else 0.0
    cart_abandonment_rate = round(((add_to_cart_events - orders_completed) / add_to_cart_events * 100), 1) if add_to_cart_events > orders_completed else 0.0

    # Charts: 1. Sales & Orders Trend (Dual Axis / Line)
    sales_qs = delivered_orders.annotate(t=trunc_fn('created_at')).values('t').annotate(rev=Sum('total_amount'), count=Count('id')).order_by('t')
    trend_labels = [item['t'].strftime(date_format) for item in sales_qs]
    trend_revenue = [float(item['rev']) for item in sales_qs]
    trend_orders = [item['count'] for item in sales_qs]

    # Charts: 2. Order Status Breakdown (Donut)
    status_qs = period_orders.values('status').annotate(count=Count('id'))
    status_labels = [s['status'] for s in status_qs]
    status_data = [s['count'] for s in status_qs]

    # Charts: 3. Top Products by Revenue & Volume
    top_items = OrderItem.objects.filter(order__created_at__gte=start_time).values('product_name', 'product_code').annotate(
        qty=Sum('quantity'),
        total_rev=Sum(F('quantity') * F('price'))
    ).order_by('-total_rev')[:6]
    top_prod_labels = [item['product_name'][:18] for item in top_items]
    top_prod_rev = [float(item['total_rev']) for item in top_items]
    top_prod_qty = [item['qty'] for item in top_items]

    # Charts: 4. District Breakdown (Regional Demand)
    district_qs = period_orders.values('district').annotate(count=Count('id')).order_by('-count')[:6]
    district_labels = [d['district'] for d in district_qs]
    district_data = [d['count'] for d in district_qs]

    # Charts: 5. Search Queries Intelligence
    top_searches = SearchQuery.objects.filter(timestamp__gte=start_time).values('query').annotate(c=Count('id')).order_by('-c')[:8]

    # Charts: 6. Device Split
    device_qs = AnalyticsEvent.objects.filter(timestamp__gte=start_time).values('device_type').annotate(c=Count('id'))
    device_labels = [d['device_type'] or 'Desktop' for d in device_qs]
    device_data = [d['c'] for d in device_qs]

    # Funnel Dataset
    funnel_labels = ['Unique Visitors', 'Product Views', 'Added to Cart', 'Checkout Initiated', 'Completed Orders']
    funnel_data = [unique_visitors, product_views, add_to_cart_events, checkout_starts, orders_completed]

    return render(request, 'merchant/analytics.html', {
        'period': period,
        'net_revenue': net_revenue,
        'gross_pipeline': gross_pipeline,
        'aov': round(aov, 2),
        'total_orders_count': total_orders_count,
        'delivered_count': delivered_orders.count(),
        'return_rate': return_rate,
        'cancel_rate': cancel_rate,
        'delivery_success_rate': delivery_success_rate,
        'conversion_rate': conversion_rate,
        'cart_abandonment_rate': cart_abandonment_rate,
        'unique_visitors': unique_visitors,
        'top_searches': top_searches,
        
        # Charts JSON
        'trend_labels': json.dumps(trend_labels),
        'trend_revenue': json.dumps(trend_revenue),
        'trend_orders': json.dumps(trend_orders),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'top_prod_labels': json.dumps(top_prod_labels),
        'top_prod_rev': json.dumps(top_prod_rev),
        'district_labels': json.dumps(district_labels),
        'district_data': json.dumps(district_data),
        'device_labels': json.dumps(device_labels),
        'device_data': json.dumps(device_data),
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
        
        try:
            disc_val = int(request.POST.get('discount_value', 10) or 10)
        except Exception:
            disc_val = 10

        max_disc_raw = request.POST.get('max_discount', '').strip()
        min_purch_raw = request.POST.get('min_purchase', '').strip()
        limit_raw = request.POST.get('usage_limit', '').strip()

        max_disc = Decimal(max_disc_raw) if max_disc_raw else None
        min_purch = Decimal(min_purch_raw) if min_purch_raw else None
        usage_limit = int(limit_raw) if limit_raw else None
        expiry = request.POST.get('expiry_date') or None

        if code:
            PromoCode.objects.create(
                code=code, discount_type=disc_type, discount_value=disc_val,
                max_discount=max_disc, min_purchase=min_purch,
                usage_limit=usage_limit, expiry_date=expiry
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
