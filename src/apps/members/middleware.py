from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class MemberOnboardingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
            except ObjectDoesNotExist:
                profile = None
            onboarding_required = bool(profile and request.user.role == "member" and not profile.onboarding_complete)
            if onboarding_required:
                onboarding_path = reverse("members:onboarding")
                allowed_prefixes = (
                    onboarding_path,
                    reverse("accounts:logout"),
                    "/static/",
                    "/media/",
                    "/offline",
                )
                if not request.path.startswith(allowed_prefixes):
                    return redirect("members:onboarding")

            pending_member_limited_access = bool(
                profile
                and request.user.role == "member"
                and profile.status == "pending"
                and profile.onboarding_complete
            )
            if pending_member_limited_access:
                allowed_prefixes = (
                    reverse("core:dashboard"),
                    reverse("members:profile"),
                    reverse("finance:dashboard"),
                    reverse("finance:invoice_list"),
                    reverse("finance:payment_list"),
                    reverse("finance:mandate_create"),
                    reverse("accounts:logout"),
                    "/finance/invoices/",
                    "/finance/payments/",
                    "/media/",
                    "/static/",
                    "/offline",
                )
                if not request.path.startswith(allowed_prefixes):
                    messages.info(
                        request,
                        "Dein Zugang bleibt bis zur Freigabe durch den Vorstand auf Dashboard, Profil und Finanzen beschraenkt.",
                    )
                    return redirect("core:dashboard")

        return self.get_response(request)
