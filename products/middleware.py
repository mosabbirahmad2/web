from .models import AnalyticsEvent

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not path.startswith('/static/') and not path.startswith('/media/'):
            ua = request.META.get('HTTP_USER_AGENT', '')
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip:
                ip = ip.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

            device = 'Mobile' if any(w in ua.lower() for w in ['mobile', 'android', 'iphone']) else 'Desktop'
            browser = 'Chrome' if 'chrome' in ua.lower() else ('Firefox' if 'firefox' in ua.lower() else 'Safari' if 'safari' in ua.lower() else 'Other')

            try:
                AnalyticsEvent.objects.create(
                    ip_address=ip,
                    user_agent=ua[:200],
                    device_type=device,
                    browser=browser,
                    path=path[:250],
                    referrer=request.META.get('HTTP_REFERER', '')[:250]
                )
            except Exception:
                pass

        return self.get_response(request)
