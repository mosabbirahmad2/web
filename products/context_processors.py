from .models import SiteSetting, Category

def site_settings_processor(request):
    return {
        'site_setting': SiteSetting.get_settings(),
        'global_categories': Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('subcategories')
    }
