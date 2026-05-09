from django.db import models
from django.contrib.auth.models import User
import random


# -----------------------------------
# CUSTOMER PROFILE (KYC DETAILS)
# -----------------------------------
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    mobile = models.CharField(max_length=10, unique=True)
    address = models.TextField()

    aadhaar = models.CharField(max_length=12, unique=True)
    pan = models.CharField(max_length=10, unique=True)

    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)

    is_kyc_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# -----------------------------------
# ACCOUNT MODEL
# -----------------------------------
class Account(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('BLOCKED', 'Blocked'),
        ('REJECTED', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    accno = models.CharField(max_length=12, unique=True, db_index=True)

    cname = models.CharField(max_length=50)
    email = models.EmailField()

    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # 🔥 NEW: approval tracking
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_accounts'
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def generate_accno(self):
        while True:
            acc = str(random.randint(100000000000, 999999999999))
            if not Account.objects.filter(accno=acc).exists():
                return acc

    def save(self, *args, **kwargs):
        if not self.accno:
            self.accno = self.generate_accno()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cname} - {self.accno} - {self.status}"
# -----------------------------------
# TRANSACTION MODEL
# -----------------------------------
class Transaction(models.Model):

    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
        ('TRANSFER', 'Transfer'),
    )

    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    receiver_accno = models.CharField(max_length=12, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='SUCCESS'
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.status}"