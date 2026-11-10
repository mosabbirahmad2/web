from .models import AnalyticsEvent

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # Exclude static, media, default admin AND custom merchant admin to avoid polluting client analytics!
        if (not path.startswith('/static/') and 
            not path.startswith('/media/') and 
            not path.startswith('/django-admin/') and 
            not path.startswith('/mosabbiradmin/')):
            
            ua = request.META.get('HTTP_USER_AGENT', '')
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip:
                ip = ip.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

            ua_lower = ua.lower()
            device = 'Mobile' if any(w in ua_lower for w in ['mobile', 'android', 'iphone']) else 'Desktop'
            if 'chrome' in ua_lower and 'edg' not in ua_lower:
                browser = 'Chrome'
            elif 'firefox' in ua_lower:
                browser = 'Firefox'
            elif 'safari' in ua_lower and 'chrome' not in ua_lower:
                browser = 'Safari'
            elif 'edg' in ua_lower:
                browser = 'Edge'
            else:
                browser = 'Other'

            try:
                AnalyticsEvent.objects.create(
                    ip_address=ip,
                    user_agent=ua[:200],
                    device_type=device,
                    browser=browser,
                    path=path[:250],
                    event_type='visit',
                    referrer=request.META.get('HTTP_REFERER', '')[:250]
                )
            except Exception:
                pass

        return self.get_response(request)
