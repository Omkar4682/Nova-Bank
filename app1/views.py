from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from functools import wraps

from .models import Account, Transaction, CustomerProfile
from .forms import RegisterForm, TransactionForm, TransferForm


# -------------------------------------------------------
# DECORATORS
# -------------------------------------------------------

def staff_required(view_func):
    """Allows only staff (is_staff=True) users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            raise PermissionDenied("Staff only area.")
        return view_func(request, *args, **kwargs)
    return wrapper


def customer_required(view_func):
    """Allows only normal customers (not staff, not superuser)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_staff or request.user.is_superuser:
            raise PermissionDenied("Customer only area.")
        return view_func(request, *args, **kwargs)
    return wrapper


# -------------------------------------------------------
# REGISTER (Public — anyone can register as a customer)
# -------------------------------------------------------
class RegisterView(View):

    def get(self, request):
        return render(request, "register.html", {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            CustomerProfile.objects.create(
                user=user,
                mobile=form.cleaned_data['mobile'],
                address=form.cleaned_data['address'],
                aadhaar=form.cleaned_data['aadhaar'],
                pan=form.cleaned_data['pan'],
                photo=form.cleaned_data.get('photo')
            )

            Account.objects.create(
                user=user,
                cname=user.username,
                email=user.email,
                status='PENDING'
            )

            return redirect('login')

        return render(request, "register.html", {"form": form})


# -------------------------------------------------------
# LOGIN — one page for all roles
# -------------------------------------------------------
class LoginView(View):

    def get(self, request):
        if request.user.is_authenticated:
            return self._redirect_by_role(request.user)
        return render(request, "login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return self._redirect_by_role(user)

        return render(request, "login.html", {"error": "Invalid username or password"})

    def _redirect_by_role(self, user):
        if user.is_superuser:
            return redirect('/admin/')
        elif user.is_staff:
            return redirect('staff_dashboard')
        else:
            return redirect('customer_dashboard')


# -------------------------------------------------------
# LOGOUT
# -------------------------------------------------------
def logout_view(request):
    logout(request)
    return redirect('login')


# -------------------------------------------------------
# CUSTOMER DASHBOARD (read-only: profile + balance + history)
# -------------------------------------------------------
@method_decorator([login_required, customer_required], name='dispatch')
class CustomerDashboardView(View):

    def get(self, request):
        account = Account.objects.filter(user=request.user).first()

        if account:
            account.refresh_from_db()

        transactions = Transaction.objects.filter(
            account=account
        ).order_by('-timestamp')[:10] if account else []

        profile = CustomerProfile.objects.filter(user=request.user).first()

        return render(request, "customer_dashboard.html", {
            "account": account,
            "transactions": transactions,
            "profile": profile,
        })


# -------------------------------------------------------
# STAFF DASHBOARD
# -------------------------------------------------------
@method_decorator([login_required, staff_required], name='dispatch')
class StaffDashboardView(View):

    def get(self, request):
        pending_accounts = Account.objects.filter(status='PENDING')
        total_customers = Account.objects.count()
        active_accounts = Account.objects.filter(status='ACTIVE').count()

        return render(request, "staff_dashboard.html", {
            "pending_accounts": pending_accounts,
            "total_customers": total_customers,
            "active_accounts": active_accounts,
        })


# -------------------------------------------------------
# APPROVE / REJECT ACCOUNTS (Staff only)
# -------------------------------------------------------
@method_decorator([login_required, staff_required], name='dispatch')
class ApproveAccountView(View):

    def get(self, request):
        accounts = Account.objects.filter(status='PENDING')
        return render(request, "approve_accounts.html", {"accounts": accounts})

    def post(self, request):
        accno = request.POST.get('accno')
        action = request.POST.get('action')  # 'approve' or 'reject'

        try:
            account = Account.objects.get(accno=accno)

            if action == 'approve':
                account.status = 'ACTIVE'
                account.approved_by = request.user
                account.approved_at = timezone.now()
                account.save()
            elif action == 'reject':
    # Delete account, profile, and user completely
                user = account.user
                account.delete()
                CustomerProfile.objects.filter(user=user).delete()
                user.delete()

        except Account.DoesNotExist:
            pass

        return redirect('approve_accounts')


# -------------------------------------------------------
# STAFF: CREATE CUSTOMER
# -------------------------------------------------------
@method_decorator([login_required, staff_required], name='dispatch')
class StaffCreateCustomerView(View):

    def get(self, request):
        return render(request, "staff_create_customer.html", {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            CustomerProfile.objects.create(
                user=user,
                mobile=form.cleaned_data['mobile'],
                address=form.cleaned_data['address'],
                aadhaar=form.cleaned_data['aadhaar'],
                pan=form.cleaned_data['pan'],
                photo=form.cleaned_data.get('photo')
            )

            # Staff-created accounts are auto-approved
            Account.objects.create(
                user=user,
                cname=user.username,
                email=user.email,
                status='ACTIVE',
                approved_by=request.user,
                approved_at=timezone.now()
            )

            return redirect('staff_dashboard')

        return render(request, "staff_create_customer.html", {"form": form})


# -------------------------------------------------------
# TRANSACTION: DEPOSIT / WITHDRAW (Staff only)
# -------------------------------------------------------
@method_decorator([login_required, staff_required], name='dispatch')
class TransactionView(View):

    def get(self, request):
        return render(request, "transaction.html", {"form": TransactionForm()})

    @transaction.atomic
    def post(self, request):
        form = TransactionForm(request.POST)

        if not form.is_valid():
            return render(request, "transaction.html", {"form": form})

        accno = form.cleaned_data['accno']
        ttype = form.cleaned_data['ttype']
        amount = form.cleaned_data['amount']

        account = Account.objects.select_for_update().filter(accno=accno).first()

        if not account:
            return render(request, "transaction.html", {
                "error": "Account not found.",
                "form": form
            })

        if account.status != 'ACTIVE':
            return render(request, "transaction.html", {
                "error": f"Account is {account.status}. Cannot process transaction.",
                "form": form
            })

        if ttype == "DEPOSIT":
            account.balance += amount

        elif ttype == "WITHDRAW":
            if amount > account.balance:
                return render(request, "transaction.html", {
                    "error": "Insufficient balance.",
                    "form": form
                })
            account.balance -= amount

        account.save()

        Transaction.objects.create(
            account=account,
            performed_by=request.user,
            amount=amount,
            transaction_type=ttype
        )

        return render(request, "transaction.html", {
            "form": TransactionForm(),
            "success": f"{ttype.capitalize()} of ₹{amount} successful. New balance: ₹{account.balance}"
        })


# -------------------------------------------------------
# TRANSFER (Staff only)
# -------------------------------------------------------
@method_decorator([login_required, staff_required], name='dispatch')
class TransferView(View):

    def get(self, request):
        return render(request, "transfer.html", {"form": TransferForm()})

    @transaction.atomic
    def post(self, request):
        form = TransferForm(request.POST)

        if not form.is_valid():
            return render(request, "transfer.html", {"form": form})

        sender_accno = form.cleaned_data['sender']
        receiver_accno = form.cleaned_data['receiver']
        amount = form.cleaned_data['amount']

        sender = Account.objects.select_for_update().filter(accno=sender_accno).first()
        receiver = Account.objects.select_for_update().filter(accno=receiver_accno).first()

        if not sender:
            return render(request, "transfer.html", {
                "error": "Sender account not found.",
                "form": form
            })

        if not receiver:
            return render(request, "transfer.html", {
                "error": "Receiver account not found.",
                "form": form
            })

        if sender.status != 'ACTIVE':
            return render(request, "transfer.html", {
                "error": f"Sender account is {sender.status}.",
                "form": form
            })

        if receiver.status != 'ACTIVE':
            return render(request, "transfer.html", {
                "error": f"Receiver account is {receiver.status}.",
                "form": form
            })

        if sender.balance < amount:
            return render(request, "transfer.html", {
                "error": "Insufficient balance in sender account.",
                "form": form
            })

        sender.balance -= amount
        receiver.balance += amount
        sender.save()
        receiver.save()

        # Debit record for sender
        Transaction.objects.create(
            account=sender,
            performed_by=request.user,
            receiver_accno=receiver.accno,
            amount=amount,
            transaction_type='TRANSFER'
        )

        # Credit record for receiver
        Transaction.objects.create(
            account=receiver,
            performed_by=request.user,
            receiver_accno=sender.accno,
            amount=amount,
            transaction_type='DEPOSIT'
        )

        return render(request, "transfer.html", {
            "form": TransferForm(),
            "success": f"₹{amount} transferred from {sender.cname} to {receiver.cname} successfully."
        })


# -------------------------------------------------------
# BALANCE VIEW
# -------------------------------------------------------
@method_decorator(login_required, name='dispatch')
class BalanceView(View):

    def get(self, request):
        # Staff: can search any account
        if request.user.is_staff:
            accno = request.GET.get('accno', '').strip()
            accounts = []

            if accno:
                accounts = Account.objects.filter(accno=accno)
            else:
                accounts = Account.objects.all().order_by('-created_at')

            return render(request, "staff_balance.html", {
                "accounts": accounts,
                "accno": accno
            })

        # Customer: only their own balance
        account = Account.objects.filter(user=request.user).first()
        return render(request, "balance.html", {"account": account})


# -------------------------------------------------------
# TRANSACTION HISTORY
# -------------------------------------------------------
@method_decorator(login_required, name='dispatch')
class TransactionHistoryView(View):

    def get(self, request):
        # Staff: can search any account's history
        if request.user.is_staff:
            accno = request.GET.get('accno', '').strip()
            transactions = []
            account = None

            if accno:
                account = Account.objects.filter(accno=accno).first()
                if account:
                    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')
                else:
                    return render(request, "staff_history.html", {
                        "error": "Account not found.",
                        "accno": accno
                    })

            return render(request, "staff_history.html", {
                "transactions": transactions,
                "account": account,
                "accno": accno
            })

        # Customer: only their own history
        account = Account.objects.filter(user=request.user).first()
        transactions = Transaction.objects.filter(account=account).order_by('-timestamp') if account else []

        return render(request, "history.html", {
            "transactions": transactions,
            "account": account
        })