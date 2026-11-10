import csv
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
