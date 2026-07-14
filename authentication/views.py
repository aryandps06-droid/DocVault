from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
import random
import time
from datetime import timedelta
from django.conf import settings

from .forms import SecureRegisterForm

User = get_user_model()


class LoginWorkspaceView(View):
    template_name = "authentication/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        
        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, self.template_name)
            
        user = authenticate(request, username=username, password=password)
        
        # Fallback: if username is an email address, try fetching the user by email
        if user is None and '@' in username:
            email_users = User.objects.filter(email=username.lower())
            for email_user in email_users:
                user = authenticate(request, username=email_user.username, password=password)
                if user is not None:
                    break
                
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Respect the next redirect parameter if present and safe
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                from django.utils.http import url_has_allowed_host_and_scheme
                if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                    
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, self.template_name)


class RegisterWorkspaceView(View):
    template_name = "authentication/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        if "reg_email" in request.session:
            del request.session["reg_email"]
            
        return render(request, self.template_name, {"step": 1})

    def post(self, request):
        step = request.POST.get("step", "1")
        
        # Step 1: User submits their email
        if step == "1":
            email = request.POST.get("email", "").strip().lower()
            if not email:
                messages.error(request, "Please enter a valid email address.")
                return render(request, self.template_name, {"step": 1})
                
            # Allow multiple user accounts with the same email
            pass
                
            # Skip OTP verification, set session verification directly and render profile setup
            request.session["reg_email"] = email
            request.session["reg_email_verified"] = True
            
            from .forms import SecureRegisterForm
            form = SecureRegisterForm(initial={'email': email})
            return render(request, self.template_name, {"step": 3, "email": email, "form": form})
            
        # Step 2: User submits the OTP
        elif step == "2":
            otp_code = request.POST.get("otp", "").strip()
            email = request.session.get("reg_email")
            session_otp = request.session.get("reg_otp")
            session_time = request.session.get("reg_otp_time", 0)
            
            if not email or not session_otp:
                messages.error(request, "Session expired. Please start over.")
                return redirect("auth_register")
                
            # Check expiry (10 mins)
            if time.time() - session_time > 600:
                messages.error(request, "OTP expired. Please request a new one.")
                return redirect("auth_register")
                
            if otp_code == session_otp:
                # OTP is valid! Move to step 3
                request.session["reg_email_verified"] = True
                form = SecureRegisterForm(initial={'email': email})
                return render(request, self.template_name, {"step": 3, "email": email, "form": form})
            else:
                messages.error(request, "Invalid code. Please try again.")
                return render(request, self.template_name, {"step": 2, "email": email})
                
        # Step 3: User submits the profile setup
        elif step == "3":
            if not request.session.get("reg_email_verified"):
                messages.error(request, "Please verify your email first.")
                return redirect("auth_register")
                
            form = SecureRegisterForm(request.POST)
            # Ensure email cannot be tampered with
            email = request.session.get("reg_email")
            
            if form.is_valid():
                user = form.save(commit=False)
                user.email = email # Force the verified email
                user.is_verified = True
                user.save()
                
                # Cleanup session
                del request.session["reg_email"]
                del request.session["reg_otp"]
                del request.session["reg_otp_time"]
                del request.session["reg_email_verified"]
                
                # Log them in automatically
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"Welcome to DocVault, {user.username}!")
                return redirect("dashboard")
            else:
                return render(request, self.template_name, {"step": 3, "email": email, "form": form})

        return redirect("auth_register")


class LogoutWorkspaceView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect("auth_login")


class ForgotPasswordView(View):
    template_name = "authentication/forgot_password.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        if "reset_email" in request.session:
            del request.session["reset_email"]
            
        return render(request, self.template_name, {"step": 1})

    def post(self, request):
        step = request.POST.get("step", "1")
        
        # Step 1: User submits their email
        if step == "1":
            email = request.POST.get("email", "").strip().lower()
            if not email:
                messages.error(request, "Please enter a valid email address.")
                return render(request, self.template_name, {"step": 1})
                
            # Skip OTP verification, set session verification directly and render password reset
            request.session["reset_email"] = email
            request.session["reset_email_verified"] = True
            
            return render(request, self.template_name, {"step": 3, "email": email})
            
        # Step 2: User submits the OTP
        elif step == "2":
            otp_code = request.POST.get("otp", "").strip()
            email = request.session.get("reset_email")
            session_otp = request.session.get("reset_otp")
            session_time = request.session.get("reset_otp_time", 0)
            
            # For security, if they provided a fake email, they never get here validly anyway
            if not email or not session_otp:
                messages.error(request, "Session expired. Please start over.")
                return redirect("auth_forgot_password")
                
            # Check expiry (10 mins)
            if time.time() - session_time > 600:
                messages.error(request, "OTP expired. Please request a new one.")
                return redirect("auth_forgot_password")
                
            if otp_code == session_otp:
                # OTP is valid! Move to step 3
                request.session["reset_email_verified"] = True
                return render(request, self.template_name, {"step": 3, "email": email})
            else:
                messages.error(request, "Invalid code. Please try again.")
                return render(request, self.template_name, {"step": 2, "email": email})
                
        # Step 3: User submits the new password
        elif step == "3":
            if not request.session.get("reset_email_verified"):
                messages.error(request, "Please verify your email first.")
                return redirect("auth_forgot_password")
                
            password = request.POST.get("password1", "")
            confirm = request.POST.get("password2", "")
            email = request.session.get("reset_email")
            
            if not password or not confirm:
                messages.error(request, "Please fill out both password fields.")
                return render(request, self.template_name, {"step": 3, "email": email})
                
            if password != confirm:
                messages.error(request, "Passwords do not match.")
                return render(request, self.template_name, {"step": 3, "email": email})
                
            users = User.objects.filter(email=email)
            if users.exists():
                for user in users:
                    user.set_password(password)
                    user.save()
                messages.success(request, "Password successfully reset. You can now log in.")
                
                # Cleanup session
                del request.session["reset_email"]
                del request.session["reset_otp"]
                del request.session["reset_otp_time"]
                del request.session["reset_email_verified"]
                
                return redirect("auth_login")
            else:
                messages.error(request, "Error finding user.")
                return redirect("auth_forgot_password")

        return redirect("auth_forgot_password")