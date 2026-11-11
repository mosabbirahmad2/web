from django.core.cache import cache
from .models import SiteSetting, Category

def site_settings_processor(request):
    site_setting = cache.get('global_site_settings')
    if not site_setting:
        site_setting = SiteSetting.get_settings()
        cache.set('global_site_settings', site_setting, timeout=300)

    global_categories = cache.get('global_active_categories')
    if global_categories is None:
        global_categories = list(
            Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('subcategories')
        )
        cache.set('global_active_categories', global_categories, timeout=300)

    return {
        'site_setting': site_setting,
        'global_categories': global_categories
    }
