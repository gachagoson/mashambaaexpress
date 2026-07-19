from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, AuditLog
from .forms import LoginForm, UserForm
from .decorators import admin_required
from .middleware import log_action


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_action(user, AuditLog.ACTION_LOGIN, request=request)
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    log_action(request.user, AuditLog.ACTION_LOGOUT, request=request)
    logout(request)
    return redirect('accounts:login')


@admin_required
def user_list(request):
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})


@admin_required
def user_create(request):
    form = UserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        log_action(request.user, AuditLog.ACTION_CREATE, 'User', user.pk, f'Created user {user.username}', request)
        messages.success(request, f'User {user.username} created.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Add worker'})


@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_action(request.user, AuditLog.ACTION_UPDATE, 'User', user.pk, f'Updated user {user.username}', request)
        messages.success(request, 'User updated.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': f'Edit {user.username}'})


@admin_required
def audit_log(request):
    logs = AuditLog.objects.select_related('user').all()[:200]
    return render(request, 'accounts/audit_log.html', {'logs': logs})
