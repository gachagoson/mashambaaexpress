from django import forms
from .models import ShopCustomer


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Create password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password"}),
    )

    class Meta:
        model = ShopCustomer
        fields = ["full_name", "email", "phone", "location"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Your full name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email address"}),
            "phone": forms.TextInput(attrs={"placeholder": "e.g. 0712 345 678"}),
            "location": forms.TextInput(
                attrs={"placeholder": "Estate / area, Nairobi"}
            ),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"placeholder": "Email address", "autofocus": True}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )


class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(
        label="Delivery address",
        widget=forms.Textarea(
            attrs={"rows": 2, "placeholder": "Street, estate, area, Nairobi"}
        ),
    )
    delivery_phone = forms.CharField(
        label="M-Pesa phone number",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "0712 345 678"}),
        help_text="We will send an M-Pesa payment prompt to this number.",
    )
    notes = forms.CharField(
        label="Order notes (optional)",
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 2, "placeholder": "Any special instructions…"}
        ),
    )
