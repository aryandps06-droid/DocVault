import os
from django.contrib.auth import get_user_model, login
from django.utils.deprecation import MiddlewareMixin

class AutoLoginMiddleware(MiddlewareMixin):
    """
    Middleware that automatically logs in any visitor as the default superuser.
    This bypasses the login page completely and prevents redirects/wrong password errors on Vercel.
    """
    def process_request(self, request):
        # 1. If the user is already authenticated, do nothing
        if request.user.is_authenticated:
            return None
            
        User = get_user_model()
        try:
            # 2. Get the first superuser (admin/aryan9)
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                # Fallback to the first available user if no superuser exists
                user = User.objects.first()
                
            if user:
                # 3. Log them in automatically
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        except Exception as e:
            print(f"Error in AutoLoginMiddleware: {e}")
            
        return None
