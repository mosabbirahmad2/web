from .models import AnalyticsEvent

BOT_USER_AGENTS = (
    'bot', 'crawl', 'spider', 'slurp', 'facebookexternalhit',
    'whatsapp', 'curl', 'python-requests', 'postman', 'headlesschrome', 'semrush'
)

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        method = request.method

        if (method == 'GET' and 
            not path.startswith('/static/') and 
            not path.startswith('/media/') and 
            not path.startswith('/django-admin/') and 
            not path.startswith('/mosabbiradmin/') and
            not path.startswith('/api/') and
            path not in ('/favicon.ico', '/robots.txt')):
            
            ua = request.META.get('HTTP_USER_AGENT', '')
            ua_lower = ua.lower()

            if not any(b in ua_lower for b in BOT_USER_AGENTS):
                ip = request.META.get('HTTP_X_FORWARDED_FOR')
                if ip:
                    ip = ip.split(',')[0].strip()
                else:
                    ip = request.META.get('REMOTE_ADDR')

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
