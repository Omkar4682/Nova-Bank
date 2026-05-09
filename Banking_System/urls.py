from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from app1.views import (
    RegisterView,
    LoginView,
    logout_view,
    CustomerDashboardView,
    StaffDashboardView,
    StaffCreateCustomerView,
    ApproveAccountView,
    TransactionView,
    TransferView,
    BalanceView,
    TransactionHistoryView,
)

urlpatterns = [
     path("admin/logout/", auth_views.LogoutView.as_view(next_page="/"), name="admin_logout"),
    
    path("admin/", admin.site.urls),
    path("", LoginView.as_view(), name="login"),
    path("admin/", admin.site.urls),
   
    # Auth
    path("", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", logout_view, name="logout"),

    # Customer
    path("customer-dashboard/", CustomerDashboardView.as_view(), name="customer_dashboard"),
    path("balance/", BalanceView.as_view(), name="balance"),
    path("history/", TransactionHistoryView.as_view(), name="history"),
    path("transaction-history/", TransactionHistoryView.as_view(), name="transaction_history"),

    # Staff
    path("staff-dashboard/", StaffDashboardView.as_view(), name="staff_dashboard"),
    path("approve-accounts/", ApproveAccountView.as_view(), name="approve_accounts"),
    path("create-customer/", StaffCreateCustomerView.as_view(), name="staff_create_customer"),
    path("transaction/", TransactionView.as_view(), name="transaction"),
    path("transfer/", TransferView.as_view(), name="transfer"),
    path("staff-balance/", BalanceView.as_view(), name="staff_balance"),
    path("staff-history/", TransactionHistoryView.as_view(), name="staff_history"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)