import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpResponse
from .models import Category, Product, Order, AnalyticsEvent, ProductImage, PromoCode

# --- AUTHENTICATION VIEWS ---
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('merchant_dashboard')

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        user = authenticate(request, username=u, password=p)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next') or 'merchant_dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'admin_custom/login.html')

def admin_logout_view(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('admin_login')

# --- CUSTOMER VIEWS (NO ADMIN LINK HERE) ---
def home_view(request):
    categories = Category.objects.filter(is_active=True, parent__isnull=True)[:8]
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    return render(request, 'index.html', {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
    })

def shop_category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_active=True)
    return render(request, 'shop/category_products.html', {'category': category, 'products': products})

def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.views_count += 1
    product.save(update_fields=['views_count'])
    return render(request, 'shop/category_products.html', {
        'category': product.category,
        'products': [product]
    })

# --- MERCHANT ADMIN VIEWS (ZATIQEASY STYLE) ---
@login_required(login_url='admin_login')
def merchant_dashboard(request):
    total_sales = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_visitors = AnalyticsEvent.objects.values('ip_address').distinct().count()
    recent_orders = Order.objects.order_by('-created_at')[:5]

    return render(request, 'merchant/dashboard.html', {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_visitors': total_visitors,
        'recent_orders': recent_orders,
        'active_menu': 'dashboard',
    })

@login_required(login_url='admin_login')
def merchant_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        short_description = request.POST.get('short_description', '').strip()
        banner = request.FILES.get('banner')
        image = request.FILES.get('image')

        if name:
            Category.objects.create(
                name=name,
                short_description=short_description,
                banner=banner,
                image=image
            )
            messages.success(request, f'Category "{name}" created successfully!')
        return redirect('merchant_categories')

    search_query = request.GET.get('q', '')
    categories = Category.objects.filter(parent__isnull=True)
    if search_query:
        categories = categories.filter(name__icontains=search_query)

    return render(request, 'merchant/categories.html', {
        'categories': categories,
        'search_query': search_query,
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
            if 'banner' in request.FILES:
                category.banner = request.FILES['banner']
            if 'image' in request.FILES:
                category.image = request.FILES['image']
            category.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('merchant_category_detail', pk=category.pk)

        elif action == 'update_subcategory':
            sub_category = get_object_or_404(Category, pk=request.POST.get('sub_pk'))
            sub_category.name = request.POST.get('name', sub_category.name).strip()
            sub_category.short_description = request.POST.get('short_description', sub_category.short_description).strip()
            if 'banner' in request.FILES:
                sub_category.banner = request.FILES['banner']
            if 'image' in request.FILES:
                sub_category.image = request.FILES['image']
            sub_category.save()
            messages.success(request, 'Sub-category updated successfully!')
            return redirect('merchant_category_detail', pk=category.pk)

        elif action == 'create_subcategory':
            sub_name = request.POST.get('name', '').strip()
            sub_desc = request.POST.get('short_description', '').strip()
            sub_banner = request.FILES.get('banner')
            sub_image = request.FILES.get('image')
            if sub_name:
                Category.objects.create(
                    name=sub_name,
                    short_description=sub_desc,
                    banner=sub_banner,
                    image=sub_image,
                    parent=category
                )
                messages.success(request, f'Sub-category "{sub_name}" created successfully!')
            return redirect('merchant_category_detail', pk=category.pk)

    subcategories = category.subcategories.all()
    return render(request, 'merchant/category_detail.html', {
        'category': category,
        'subcategories': subcategories,
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
    if parent_id:
        return redirect('merchant_category_detail', pk=parent_id)
    return redirect('merchant_categories')

@login_required(login_url='admin_login')
def merchant_analytics(request):
    # 1. Basic Metrics
    unique_visitors = AnalyticsEvent.objects.values('ip_address').distinct().count()
    device_stats = AnalyticsEvent.objects.values('device_type').annotate(count=Count('id'))

    # 2. Revenue vs Order Count
    total_revenue = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()

    # 3. Top Performing Categories
    category_performance = Category.objects.annotate(
        total_sold=Count('products__orderitem')
    ).order_by('-total_sold')[:5]

    # 4. Order Status Distribution
    status_dist = Order.objects.values('status').annotate(count=Count('id'))

    return render(request, 'merchant/analytics.html', {
        'unique_visitors': unique_visitors,
        'device_stats': device_stats,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'category_performance': category_performance,
        'status_dist': status_dist,
        'active_menu': 'analytics',
    })

@login_required(login_url='admin_login')
def merchant_orders(request):
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()
    orders = Order.objects.all().order_by('-created_at')

    if status_filter and status_filter != 'All Orders':
        orders = orders.filter(status=status_filter)
    if search_query:
        orders = orders.filter(order_id__icontains=search_query) | orders.filter(customer_phone__icontains=search_query)

    return render(request, 'merchant/orders.html', {
        'orders': orders,
        'active_menu': 'orders',
        'status_filter': status_filter,
        'search_query': search_query,
    })

@login_required(login_url='admin_login')
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer Name', 'Phone', 'Address', 'Total Amount', 'Status', 'Date'])

    for order in Order.objects.all().order_by('-created_at'):
        writer.writerow([
            order.order_id,
            order.customer_name,
            order.customer_phone,
            order.shipping_address,
            order.total_amount,
            order.status,
            order.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    return response

@login_required(login_url='admin_login')
def update_order_status(request, pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        status = request.POST.get('status')
        if status:
            order.status = status
            order.save()
            messages.success(request, f'Order {order.order_id} updated to {status}.')
    return redirect('merchant_orders')

@login_required(login_url='admin_login')
def merchant_promos(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount = request.POST.get('discount')
        expiry = request.POST.get('expiry')
        limit = request.POST.get('limit', 100)

        if code and discount and expiry:
            PromoCode.objects.create(
                code=code,
                discount_percentage=discount,
                expiry_date=expiry,
                usage_limit=limit
            )
            messages.success(request, f'Promo code "{code}" created successfully!')
        else:
            messages.error(request, 'Please fill in all required fields.')
        return redirect('merchant_promos')

    promos = PromoCode.objects.all().order_by('-created_at')
    return render(request, 'merchant/promo.html', {
        'promos': promos,
        'active_menu': 'promo',
    })

@login_required(login_url='admin_login')
def toggle_promo(request, pk):
    promo = get_object_or_404(PromoCode, pk=pk)
    promo.is_active = not promo.is_active
    promo.save()
    return redirect('merchant_promos')

@login_required(login_url='admin_login')
def delete_promo(request, pk):
    promo = get_object_or_404(PromoCode, pk=pk)
    promo.delete()
    messages.success(request, 'Promo code deleted successfully!')
    return redirect('merchant_promos')

@login_required(login_url='admin_login')
def merchant_products(request):
    search_query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    products = Product.objects.all().order_by('-created_at')

    if search_query:
        products = products.filter(name__icontains=search_query)
    if category_id:
        products = products.filter(category_id=category_id)

    categories = Category.objects.all()
    return render(request, 'merchant/products.html', {
        'products': products,
        'categories': categories,
        'active_menu': 'products',
        'search_query': search_query,
        'selected_category': category_id,
    })

@login_required(login_url='admin_login')
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        stock = request.POST.get('stock', 20)
        is_featured = bool(request.POST.get('is_featured'))
        main_image = request.FILES.get('main_image')
        gallery_images = request.FILES.getlist('gallery_images')

        if name and category_id and price:
            category = get_object_or_404(Category, pk=category_id)
            product = Product.objects.create(
                name=name,
                category=category,
                description=description,
                price=price,
                discount_price=discount_price if discount_price else None,
                stock=stock,
                is_featured=is_featured,
                image=main_image
            )

            # Save gallery images
            for img in gallery_images[:6]:
                if img:
                    ProductImage.objects.create(product=product, image=img)

            messages.success(request, f'Product "{name}" created successfully!')
        else:
            messages.error(request, 'Please fill in all required fields.')

        return redirect('merchant_products')
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
        stock = request.POST.get('stock')
        is_featured = bool(request.POST.get('is_featured'))

        if name and category_id and price:
            product.name = name
            product.category = get_object_or_404(Category, pk=category_id)
            product.description = description
            product.price = price
            product.discount_price = discount_price if discount_price else None
            if stock:
                product.stock = int(stock)
            product.is_featured = is_featured

            if 'main_image' in request.FILES:
                product.image = request.FILES['main_image']

            product.save()

            new_gallery = request.FILES.getlist('gallery_images')
            for img in new_gallery[:6]:
                if img:
                    ProductImage.objects.create(product=product, image=img)

            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('merchant_products')
        else:
            messages.error(request, 'Please fill in required fields.')

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
