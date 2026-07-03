from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
import random
from datetime import timedelta
from django.conf import settings

from .forms import SecureRegisterForm
from users.models import EmailOTP

User = get_user_model()


class LoginWorkspaceView(View):
    template_name = "authentication/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
            
        # Clear any existing OTP session to start fresh
        if "otp_email" in request.session:
            del request.session["otp_email"]
            
        return render(request, self.template_name)

    def post(self, request):
        # Step 1: User submits their email
        if "email" in request.POST:
            email = request.POST.get("email").strip().lower()
            
            if not email:
                messages.error(request, "Please enter a valid email address.")
                return redirect("auth_login")
                
            # Auto-register if user doesn't exist to make onboarding seamless
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'is_active': True,
                    'is_verified': True
                }
            )
            
            if created:
                user.set_password(User.objects.make_random_password(length=14))
                user.save()
                
            # Generate 6-digit OTP
            otp_code = f"{random.randint(100000, 999999)}"
            
            # Save OTP to database
            EmailOTP.objects.create(
                user=user,
                otp_code=otp_code
            )
            
            # DEMO FALLBACK: Print to console
            print("="*50)
            print(f" MAGIC LOGIN CODE FOR {email}: {otp_code} ")
            print("="*50)
            
            # Send Email
            try:
                send_mail(
                    subject="DocVault - Your Verification Code",
                    message=f"Hello,\n\nYour DocVault verification code is: {otp_code}\n\nThis code will expire in {getattr(settings, 'EMAIL_OTP_EXPIRE_MINUTES', 5)} minutes.\n\nThank you.",
                    from_email="aryandps06@gmail.com",
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.info(request, f"We've sent a 6-digit code to {email}")
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.error(request, "Failed to send email. Check console logs if using Console Backend.")
                
            # Set session to remember which email is authenticating
            request.session["otp_email"] = email
            
            # Re-render template with a flag to show step 2 (OTP Input)
            return render(request, self.template_name, {"step": 2, "email": email})
            
        # Step 2: User submits the OTP
        elif "otp" in request.POST:
            otp_code = request.POST.get("otp").strip()
            email = request.session.get("otp_email")
            
            if not email:
                messages.error(request, "Session expired. Please try again.")
                return redirect("auth_login")
                
            try:
                user = User.objects.get(username=email)
                
                # Check for valid OTP
                expiry_time = timezone.now() - timedelta(minutes=getattr(settings, 'EMAIL_OTP_EXPIRE_MINUTES', 5))
                
                valid_otp = EmailOTP.objects.filter(
                    user=user,
                    otp_code=otp_code,
                    is_used=False,
                    created_at__gte=expiry_time
                ).first()
                
                if valid_otp:
                    valid_otp.is_used = True
                    valid_otp.save()
                    
                    login(request, user)
                    
                    # Clean up session
                    del request.session["otp_email"]
                    
                    messages.success(request, f"Welcome to DocVault, {user.username}!")
                    return redirect("dashboard")
                else:
                    messages.error(request, "Invalid or expired code. Please try again.")
                    return render(request, self.template_name, {"step": 2, "email": email})
                    
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect("auth_login")

        return redirect("auth_login")


class RegisterWorkspaceView(View):
    template_name = "authentication/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = SecureRegisterForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SecureRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect("auth_login")
        return render(request, self.template_name, {"form": form})


class LogoutWorkspaceView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect("auth_login")