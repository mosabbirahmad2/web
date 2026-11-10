from .models import SiteSetting

def site_settings_processor(request):
    return {
        'site_setting': SiteSetting.get_settings()
    }
