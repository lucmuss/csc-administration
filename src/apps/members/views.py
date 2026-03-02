from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User

from .forms import MemberRegistrationForm
from .models import Profile


def register(request):
    if request.method == "POST":
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registrierung erfolgreich. Freischaltung folgt nach Verifizierung.")
            return redirect("accounts:login")
    else:
        form = MemberRegistrationForm()
    return render(request, "members/register.html", {"form": form})


@login_required
def profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, "members/profile.html", {"profile": profile})


def _is_board(user: User) -> bool:
    return user.is_authenticated and user.role == User.ROLE_BOARD


@user_passes_test(_is_board)
def verify_member(request, profile_id: int):
    profile = get_object_or_404(Profile, id=profile_id)
    profile.is_verified = True
    profile.status = Profile.STATUS_ACTIVE
    profile.allocate_member_number()
    profile.save(update_fields=["is_verified", "status", "updated_at"])
    messages.success(request, f"Mitglied {profile.user.email} verifiziert")
    return redirect("core:dashboard")
