from django.contrib.auth import get_user_model

class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the user is not authenticated and is not on the public landing page, automatically log them in as the primary superuser
        if request.path != '/' and (not hasattr(request, 'user') or not request.user.is_authenticated):
            User = get_user_model()
            # Find the primary superuser (e.g. aryan9)
            superuser = User.objects.filter(username='aryan9').first() or User.objects.filter(is_superuser=True).first()
            if superuser:
                request.user = superuser
                
        response = self.get_response(request)
        return response
