from django import forms
from django.contrib.auth.models import User
from .models import CustomerProfile
import re


# -------------------------------
# REGISTER FORM
# -------------------------------
class RegisterForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)

    mobile = forms.CharField(max_length=10)
    address = forms.CharField(widget=forms.Textarea)

    aadhaar = forms.CharField(max_length=12)
    pan = forms.CharField(max_length=10)

    photo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    # -------------------------------
    # VALIDATIONS
    # -------------------------------

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError("Enter valid 10 digit mobile number")

        if CustomerProfile.objects.filter(mobile=mobile).exists():
            raise forms.ValidationError("Mobile number already exists")

        return mobile

    def clean_aadhaar(self):
        aadhaar = self.cleaned_data['aadhaar']
        if not aadhaar.isdigit() or len(aadhaar) != 12:
            raise forms.ValidationError("Aadhaar must be 12 digits")

        if CustomerProfile.objects.filter(aadhaar=aadhaar).exists():
            raise forms.ValidationError("Aadhaar already exists")

        return aadhaar

    def clean_pan(self):
        pan = self.cleaned_data['pan'].upper()

        # PAN format check: ABCDE1234F
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
        if not re.match(pattern, pan):
            raise forms.ValidationError("Invalid PAN format (ABCDE1234F)")

        if CustomerProfile.objects.filter(pan=pan).exists():
            raise forms.ValidationError("PAN already exists")

        return pan


# -------------------------------
# TRANSACTION FORM (STAFF)
# -------------------------------
class TransactionForm(forms.Form):

    TRANSACTION_CHOICES = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
    )

    accno = forms.CharField(max_length=12)
    ttype = forms.ChoiceField(choices=TRANSACTION_CHOICES)
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def clean_accno(self):
        accno = self.cleaned_data['accno']
        if not accno.isdigit() or len(accno) != 12:
            raise forms.ValidationError("Account number must be 12 digits")
        return accno

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        return amount


# -------------------------------
# TRANSFER FORM (STAFF)
# -------------------------------
class TransferForm(forms.Form):

    sender = forms.CharField(max_length=12)
    receiver = forms.CharField(max_length=12)
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        cleaned_data = super().clean()
        sender = cleaned_data.get('sender')
        receiver = cleaned_data.get('receiver')

        if sender and receiver:
            if sender == receiver:
                raise forms.ValidationError("Sender and receiver cannot be same")

        return cleaned_data

    def clean_sender(self):
        sender = self.cleaned_data['sender']
        if not sender.isdigit() or len(sender) != 12:
            raise forms.ValidationError("Sender account must be 12 digits")
        return sender

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']
        if not receiver.isdigit() or len(receiver) != 12:
            raise forms.ValidationError("Receiver account must be 12 digits")
        return receiver

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        return amount


# -------------------------------
# BALANCE FORM (OPTIONAL)
# -------------------------------
class BalanceForm(forms.Form):

    accno = forms.CharField(max_length=12)

    def clean_accno(self):
        accno = self.cleaned_data['accno']
        if not accno.isdigit() or len(accno) != 12:
            raise forms.ValidationError("Account number must be 12 digits")
        return accno