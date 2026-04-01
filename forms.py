from django import forms
from .models import Order



class QRUploadForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['qr_code']
class UploadQRCodeForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['qr_code']

class PasswordResetRequestForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)

class PasswordResetVerifyForm(forms.Form):
    otp = forms.CharField(max_length=6, required=True)
    new_password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")



from django import forms

class StaffUserForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )

class StaffOTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter OTP'})
    )

class StaffPasswordResetForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        np = cleaned_data.get("new_password")
        cp = cleaned_data.get("confirm_password")
        if np != cp:
            raise forms.ValidationError("Passwords do not match")

