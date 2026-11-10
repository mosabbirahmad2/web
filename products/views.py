import csv
import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Avg
from django.db.models.functions import TruncDate, TruncHour
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
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

# --- AUTHENTICATION (3 FAILED ATTEMPTS = 12H LOCKOUT) ---
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('merchant_dashboard')

    ip = get_client_ip(request)
    attempt, _ = AdminLoginAttempt.objects.get_or_create(ip_address=ip)

    if attempt.is_locked():
        remaining = attempt.locked_until - timezone.now()
        hours = int(remaining.total_seconds() // 3600)
        mins = int((remaining.total_seconds() % 3600) // 60)
        messages.error(request, f"Security Alert: 3 failed attempts. Your device is locked out for {hours}h {mins}m.")
        return render(request, 'admin_custom/login.html', {'locked': True})

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        user = authenticate(request, username=u, password=p)

        if user is not None and user.is_staff:
            attempt.failed_attempts = 0
            attempt.locked_until = None
            attempt.save()
            login(request, user)
            return redirect(request.GET.get('next') or 'merchant_dashboard')
        else:
            attempt.failed_attempts += 1
            if attempt.failed_attempts >= 3:
                attempt.locked_until = timezone.now() + timedelta(hours=12)
                attempt.save()
                messages.error(request, "Security Alert: 3 failed attempts. Device locked out for 12 hours!")
            else:
                attempt.save()
                messages.error(request, f"Invalid password! Remaining attempts: {3 - attempt.failed_attempts}")

    return render(request, 'admin_custom/login.html')

def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')

# --- STOREFRONT ---
def home_view(request):
    ip = get_client_ip(request)
    today = timezone.now().date()
    UniqueVisitorLog.objects.get_or_create(ip_address=ip, date=today)

    setting, _ = SiteSetting.objects.get_or_create(pk=1)
    categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('subcategories')
    showcase_sections = ShowcaseSection.objects.filter(is_active=True).prefetch_related('products')
    
    # All Products Section for Homepage (Highlighted)
    all_products = Product.objects.filter(is_active=True).select_related('category').order_by('-created_at')

    return render(request, 'index.html', {
        'site_setting': setting,
        'categories': categories,
        'showcase_sections': showcase_sections,
        'all_products': all_products,
    })

def shop_category_view(request, slug):
    setting, _ = SiteSetting.objects.get_or_create(pk=1)
    category = get_object_or_404(Category, slug=slug)
    sub_ids = category.subcategories.values_list('id', flat=True)
    products = Product.objects.filter(
        Q(category=category) | Q(category__id__in=sub_ids),
        is_active=True
    ).distinct().select_related('category')

    return render(request, 'shop/category_products.html', {
        'site_setting': setting,
        'category': category,
        'products': products
    })

# Full Dedicated Product Detail Page (Opens in Same Tab)
def product_detail_view(request, pk):
    setting, _ = SiteSetting.objects.get_or_create(pk=1)
    product = get_object_or_404(Product.objects.select_related('category').prefetch_related('images', 'reviews'), pk=pk)
    product.views_count += 1
    product.save(update_fields=['views_count'])

    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:5]

    return render(request, 'shop/product_detail.html', {
        'site_setting': setting,
        'product': product,
        'related_products': related_products,
        'reviews': product.reviews.filter(is_approved=True)
    })

@csrf_exempt
def add_product_review(request, pk):
    if request.method == 'POST':
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

@csrf_exempt
def log_event_api(request):
    if request.method == 'POST':
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
    return JsonResponse({'status': 'ok'})

@csrf_exempt
def place_order_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            district = data.get('district', 'Dhaka').strip()
            thana = data.get('thana', '').strip()
            address = data.get('address', '').strip()
            items = data.get('items', [])

            if not name or not phone or not address or not items:
                return JsonResponse({'status': 'error', 'message': 'Please fill out all delivery fields!'}, status=400)

            setting, _ = SiteSetting.objects.get_or_create(pk=1)
            is_dhaka = (district.lower() == 'dhaka')
            delivery_fee = setting.delivery_fee_dhaka if is_dhaka else setting.delivery_fee_outside

            subtotal = 0
            order = Order.objects.create(
                customer_name=name,
                customer_phone=phone,
                district=district,
                thana=thana,
                shipping_address=address,
                delivery_zone="Inside Dhaka" if is_dhaka else "Outside Dhaka",
                delivery_fee=delivery_fee,
                status='Placed',
                total_amount=0
            )

            for item in items:
                prod = Product.objects.filter(id=item.get('id')).first()
                if prod:
                    qty = int(item.get('qty', 1))
                    price = prod.effective_price
                    OrderItem.objects.create(order=order, product=prod, quantity=qty, price=price)
                    subtotal += (price * qty)

            order.total_amount = subtotal + float(delivery_fee)
            order.save()

            AnalyticsEvent.objects.create(
                ip_address=get_client_ip(request),
                path='/checkout/success',
                event_type='order_completed'
            )

            return JsonResponse({
                'status': 'success', 
                'order_id': order.order_id, 
                'total': str(order.total_amount)
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# --- ADMIN PANEL ---
@login_required(login_url='admin_login')
def merchant_dashboard(request):
    total_sales = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_visitors = UniqueVisitorLog.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:6]

    return render(request, 'merchant/dashboard.html', {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_visitors': total_visitors,
        'recent_orders': recent_orders,
        'active_menu': 'dashboard',
    })

# Orders Page (Image 1)
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

    today = timezone.now().date()
    confirmed_orders = Order.objects.filter(status='Confirmed').count()
    total_amount = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_customers = Order.objects.values('customer_phone').distinct().count()

    return render(request, 'merchant/orders.html', {
        'orders': orders,
        'active_menu': 'orders',
        'status_filter': status_filter,
        'search_query': search_query,
        'confirmed_orders': confirmed_orders,
        'total_amount': total_amount,
        'total_customers': total_customers,
        'today_str': today.strftime('%dth %B'),
    })

@login_required(login_url='admin_login')
def update_order_status(request, pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        status = request.POST.get('status')
        if status:
            order.status = status
            order.save()
            messages.success(request, f'Order {order.order_id} status updated to {status}.')
    return redirect('merchant_orders')

@login_required(login_url='admin_login')
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Phone', 'District', 'Thana', 'Address', 'Delivery Fee', 'Total', 'Status', 'Date'])
    for o in Order.objects.all().order_by('-created_at'):
        writer.writerow([o.order_id, o.customer_name, o.customer_phone, o.district, o.thana or '', o.shipping_address, o.delivery_fee, o.total_amount, o.status, o.created_at.strftime('%Y-%m-%d %H:%M')])
    return response

# Customers Page (Image 6)
@login_required(login_url='admin_login')
def merchant_customers(request):
    search = request.GET.get('q', '').strip()
    customers = Order.objects.values('customer_name', 'customer_phone').annotate(
        orders_count=Count('id'),
        total_spent=Sum('total_amount')
    ).order_by('-orders_count')

    if search:
        customers = customers.filter(Q(customer_name__icontains=search) | Q(customer_phone__icontains=search))

    return render(request, 'merchant/customers.html', {
        'customers': customers,
        'total_count': customers.count(),
        'active_menu': 'customers',
    })

# Products Page (Image 2)
@login_required(login_url='admin_login')
def merchant_products(request):
    search = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category', '').strip()
    products = Product.objects.all().select_related('category').order_by('-created_at')

    if search:
        products = products.filter(name__icontains=search)
    if cat_id:
        products = products.filter(category_id=cat_id)

    categories = Category.objects.all()
    return render(request, 'merchant/products.html', {
        'products': products,
        'categories': categories,
        'active_menu': 'products',
        'search_query': search,
        'selected_category': cat_id,
    })

@login_required(login_url='admin_login')
def add_product(request):
    if request.method == 'POST':
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
            d_price = float(discount_price) if discount_price else None
            r_price = float(price)
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
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        stock = request.POST.get('stock', 50)
        badge_tag = request.POST.get('badge_tag', '').strip()
        is_featured = bool(request.POST.get('is_featured'))

        if name and category_id and price:
            product.name = name
            product.category = get_object_or_404(Category, pk=category_id)
            product.description = description
            r_price = float(price)
            d_price = float(discount_price) if discount_price else None
            if d_price and d_price > r_price:
                d_price = r_price
            product.price = r_price
            product.discount_price = d_price
            product.stock = int(stock)
            product.badge_tag = badge_tag
            product.is_featured = is_featured

            if 'main_image' in request.FILES:
                product.image = request.FILES['main_image']

            product.save()

            for g_img in request.FILES.getlist('gallery_images'):
                ProductImage.objects.create(product=product, image=g_img)

            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('merchant_products')

    return render(request, 'merchant/products.html', {
        'products': Product.objects.all().order_by('-created_at'),
        'categories': categories,
        'edit_product': product,
        'active_menu': 'products',
    })

@login_required(login_url='admin_login')
def merchant_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f'Product "{name}" deleted successfully!')
    return redirect('merchant_products')

# Categories (Images 3, 4, 5)
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
def merchant_toggle_category(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    cat.is_active = not cat.is_active
    cat.save()
    return redirect(request.META.get('HTTP_REFERER', 'merchant_categories'))

@login_required(login_url='admin_login')
def merchant_delete_category(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    parent_id = cat.parent.pk if cat.parent else None
    cat.delete()
    messages.success(request, 'Category deleted successfully!')
    return redirect('merchant_category_detail', pk=parent_id) if parent_id else redirect('merchant_categories')

# Showcase Sections (Editable)
@login_required(login_url='admin_login')
def merchant_sections(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        bg_style = request.POST.get('background_style', 'light')
        has_countdown = bool(request.POST.get('has_countdown'))
        product_ids = request.POST.getlist('products')

        if title:
            sec = ShowcaseSection.objects.create(title=title, background_style=bg_style, has_countdown=has_countdown)
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
def merchant_edit_section(request, pk):
    sec = get_object_or_404(ShowcaseSection, pk=pk)
    if request.method == 'POST':
        sec.title = request.POST.get('title', sec.title).strip()
        sec.background_style = request.POST.get('background_style', sec.background_style)
        sec.has_countdown = bool(request.POST.get('has_countdown'))
        product_ids = request.POST.getlist('products')
        sec.products.set(product_ids)
        sec.save()
        messages.success(request, f'Section "{sec.title}" updated!')
        return redirect('merchant_sections')

    return redirect('merchant_sections')

@login_required(login_url='admin_login')
def merchant_toggle_section(request, pk):
    sec = get_object_or_404(ShowcaseSection, pk=pk)
    sec.is_active = not sec.is_active
    sec.save()
    return redirect('merchant_sections')

@login_required(login_url='admin_login')
def merchant_delete_section(request, pk):
    sec = get_object_or_404(ShowcaseSection, pk=pk)
    sec.delete()
    messages.success(request, 'Section deleted successfully!')
    return redirect('merchant_sections')

# Site Settings & Theme Customizer (Images 8 & 9)
@login_required(login_url='admin_login')
def merchant_settings(request):
    setting, _ = SiteSetting.objects.get_or_create(pk=1)
    if request.method == 'POST':
        setting.site_name = request.POST.get('site_name', setting.site_name).strip()
        setting.contact_phone = request.POST.get('contact_phone', setting.contact_phone).strip()
        setting.whatsapp_number = request.POST.get('whatsapp_number', setting.whatsapp_number).strip()
        setting.whatsapp_username = request.POST.get('whatsapp_username', setting.whatsapp_username).strip()
        setting.contact_email = request.POST.get('contact_email', setting.contact_email).strip()
        setting.office_address = request.POST.get('office_address', setting.office_address).strip()
        setting.announcement_notice = request.POST.get('announcement_notice', setting.announcement_notice).strip()
        setting.delivery_fee_dhaka = request.POST.get('delivery_fee_dhaka', setting.delivery_fee_dhaka)
        setting.delivery_fee_outside = request.POST.get('delivery_fee_outside', setting.delivery_fee_outside)
        setting.save()
        messages.success(request, 'Site settings updated successfully!')
        return redirect('merchant_settings')

    return render(request, 'merchant/settings.html', {'setting': setting, 'active_menu': 'settings'})

@login_required(login_url='admin_login')
def merchant_customize_theme(request):
    setting, _ = SiteSetting.objects.get_or_create(pk=1)
    if request.method == 'POST':
        setting.theme_color = request.POST.get('theme_color', setting.theme_color)
        setting.theme_mode = request.POST.get('theme_mode', setting.theme_mode)
        setting.enable_buy_now = (request.POST.get('enable_buy_now') == 'yes')
        setting.save()
        messages.success(request, 'Theme customization saved!')
        return redirect('merchant_customize_theme')

    return render(request, 'merchant/customize_theme.html', {'setting': setting, 'active_menu': 'themes'})

# Analytics & Reports (Image 7 + Dynamic Time Filters)
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
    paid_rev = paid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    all_time_revenue = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    avg_paid_order = paid_orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
    all_time_avg_order = Order.objects.aggregate(Avg('total_amount'))['total_amount__avg'] or 0

    visitor_to_purchase_rate = round((all_orders / unique_visitors * 100), 1) if unique_visitors > 0 else 0.0
    abandoned_carts = max(0, add_to_cart_events - all_orders)

    traffic_qs = UniqueVisitorLog.objects.filter(created_at__gte=start_time).annotate(t=trunc_fn('created_at')).values('t').annotate(c=Count('id')).order_by('t')
    chart_labels = [item['t'].strftime(date_format) for item in traffic_qs]
    chart_data = [item['c'] for item in traffic_qs]

    clicked_products = Product.objects.filter(views_count__gt=0).order_by('-views_count')[:6]
    clicked_labels = [p.name[:16] for p in clicked_products]
    clicked_data = [p.views_count for p in clicked_products]

    ordered_items = OrderItem.objects.filter(order__created_at__gte=start_time).values('product__name').annotate(qty=Sum('quantity')).order_by('-qty')[:6]
    order_labels = [item['product__name'][:16] if item['product__name'] else 'Deleted' for item in ordered_items]
    order_data = [item['qty'] for item in ordered_items]

    districts = Order.objects.filter(created_at__gte=start_time).values('district').annotate(c=Count('id')).order_by('-c')[:6]
    district_labels = [d['district'] for d in districts]
    district_data = [d['c'] for d in districts]

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
        'all_time_avg_order': round(all_time_avg_order, 2),
        'visitor_to_purchase_rate': visitor_to_purchase_rate,
        'abandoned_carts': abandoned_carts,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'clicked_labels': json.dumps(clicked_labels),
        'clicked_data': json.dumps(clicked_data),
        'order_labels': json.dumps(order_labels),
        'order_data': json.dumps(order_data),
        'district_labels': json.dumps(district_labels),
        'district_data': json.dumps(district_data),
        'active_menu': 'analytics',
    })

# Promo Codes (Images 10 & 11)
@login_required(login_url='admin_login')
def merchant_promos(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        disc_type = request.POST.get('discount_type', 'percentage')
        disc_val = request.POST.get('discount_value', 10)
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
def toggle_promo(request, pk):
    p = get_object_or_404(PromoCode, pk=pk)
    p.is_active = not p.is_active
    p.save()
    return redirect('merchant_promos')

@login_required(login_url='admin_login')
def delete_promo(request, pk):
    p = get_object_or_404(PromoCode, pk=pk)
    p.delete()
    messages.success(request, 'Promo code deleted successfully!')
    return redirect('merchant_promos')
