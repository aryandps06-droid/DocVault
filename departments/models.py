from django.db import models
from django.conf import settings

class Department(models.Model):
    class DepartmentType(models.TextChoices):
        OPERATIONS = 'OPERATIONS', 'Operations & Mining'
        ADMIN = 'ADMIN', 'Executive & Administration'
        TECH = 'TECH', 'Technology & R&D'
        SUPPORT = 'SUPPORT', 'Support & Services'
        HR = 'HR', 'Human Resources'
        FINANCE = 'FINANCE', 'Finance & Accounts'
        SAFETY = 'SAFETY', 'Safety & Compliance'

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=50,
        choices=DepartmentType.choices,
        default=DepartmentType.OPERATIONS
    )
    head_of_department = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_department'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kv_departments'

    def __str__(self):
        return self.name