from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False,
                               help_text='Leave blank to keep current password.')

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'is_active', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd  = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user
