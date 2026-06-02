from django.utils import translation

class QueryParamsLocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get('lang')
        if not lang:
            # Try to get language from Accept-Language header or X-Language header
            lang = request.headers.get('Accept-Language') or request.headers.get('X-Language')
        
        if lang:
            # Extract main language code (e.g. 'uz' from 'uz-UZ' or 'uz,ru;q=0.9')
            lang = lang.lower().split('-')[0].split(',')[0].strip()
            if lang == 'eng':
                lang = 'en'
            elif lang == 'ja':
                lang = 'jp'
            
            if lang in ['uz', 'ru', 'en', 'jp']:
                translation.activate(lang)
                request.LANGUAGE_CODE = lang

        response = self.get_response(request)
        return response
