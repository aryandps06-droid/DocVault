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
            email_user = User.objects.filter(email=username.lower()).first()
            if email_user:
                user = authenticate(request, username=email_user.username, password=password)
                
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
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
                
            if User.objects.filter(email=email).exists():
                messages.error(request, "An account with this email already exists.")
                return redirect("auth_login")
                
            # Generate 6-digit OTP
            otp_code = f"{random.randint(100000, 999999)}"
            
            # Store in session
            request.session["reg_otp"] = otp_code
            request.session["reg_otp_time"] = time.time()
            request.session["reg_email"] = email
            
            # DEMO FALLBACK: Print to console
            print("="*50)
            print(f" MAGIC REGISTRATION CODE FOR {email}: {otp_code} ")
            print("="*50)
            
            # Send Email
            try:
                send_mail(
                    subject="DocVault - Verify Your Email",
                    message=f"Hello,\n\nYour DocVault registration verification code is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nThank you.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.info(request, f"We've sent a 6-digit code to {email}")
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.warning(request, f"Email failed to send. Developer Bypass: Your code is {otp_code}")
                
            return render(request, self.template_name, {"step": 2, "email": email})
            
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
                
            user = User.objects.filter(email=email).first()
            if not user:
                # Still show success to prevent email enumeration attacks
                messages.info(request, f"If an account exists, a recovery code was sent to {email}")
                return render(request, self.template_name, {"step": 2, "email": email})
                
            # Generate 6-digit OTP
            otp_code = f"{random.randint(100000, 999999)}"
            
            # Store in session
            request.session["reset_otp"] = otp_code
            request.session["reset_otp_time"] = time.time()
            request.session["reset_email"] = email
            
            # DEMO FALLBACK: Print to console
            print("="*50)
            print(f" MAGIC RESET CODE FOR {email}: {otp_code} ")
            print("="*50)
            
            # Send Email
            try:
                send_mail(
                    subject="DocVault - Password Reset Code",
                    message=f"Hello,\n\nYour DocVault password reset code is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nThank you.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.info(request, f"We've sent a 6-digit code to {email}")
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.warning(request, f"Email failed to send. Developer Bypass: Your code is {otp_code}")
                
            return render(request, self.template_name, {"step": 2, "email": email})
            
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
                
            user = User.objects.filter(email=email).first()
            if user:
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