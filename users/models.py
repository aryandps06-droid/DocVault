from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'System Administrator'
        MANAGER = 'MANAGER', 'Department Manager'
        EMPLOYEE = 'EMPLOYEE', 'Standard Employee'
        
    role = models.CharField(
        max_length=20, 
        choices=Roles.choices, 
        default=Roles.EMPLOYEE
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    department = models.ForeignKey(
        'departments.Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='staff'
    )
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'kv_user_directory'

    def __str__(self):
        return f"{self.username} ({self.role})"

class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'kv_email_otps'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.username} - {self.otp_code}"