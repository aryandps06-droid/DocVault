from django.contrib.auth import get_user_model, login
from django.utils.deprecation import MiddlewareMixin

class StatelessSessionMiddleware(MiddlewareMixin):
    """
    Middleware that caches authenticated user data in the secure signed session cookie.
    If Vercel recycles the container and the SQLite database resets (removing the user),
    this middleware reconstructs the user record on the fly to prevent redirecting to login.
    """
    def process_request(self, request):
        User = get_user_model()
        
        # 1. If user is authenticated, sync their profile data to the session cookie
        if request.user.is_authenticated:
            user = request.user
            request.session['stateless_user_data'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'password': user.password,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
        else:
            # 2. If anonymous, check if cookie holds a secure session user cache
            user_data = request.session.get('stateless_user_data')
            if user_data:
                try:
                    # Recreate the user on the fly in the new container's SQLite DB
                    user, created = User.objects.get_or_create(
                        id=user_data['id'],
                        defaults={
                            'username': user_data['username'],
                            'email': user_data['email'],
                            'first_name': user_data['first_name'],
                            'last_name': user_data['last_name'],
                            'role': user_data['role'],
                            'password': user_data['password'],
                            'is_staff': user_data['is_staff'],
                            'is_superuser': user_data['is_superuser'],
                        }
                    )
                    
                    # Force re-authentication for this request
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                except Exception as e:
                    print(f"Error recreating stateless user: {e}")
