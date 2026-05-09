from django.contrib import admin
from .models import Account, CustomerProfile, Transaction

admin.site.site_header = "Nova Bank Administration"
admin.site.site_title = "Nova Bank Admin Portal"
admin.site.index_title = "Welcome to Nova Bank Admin"
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['accno', 'cname', 'balance', 'email']
    search_fields = ['accno', 'cname']


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'mobile', 'aadhaar', 'pan']
    search_fields = ['user__username', 'aadhaar', 'pan']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'transaction_type', 'amount', 'timestamp']
    list_filter = ['transaction_type']