from django.shortcuts import redirect
from django.urls import reverse

class MemberOnboardingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            onboarding_required = bool(profile and not profile.onboarding_complete)
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

        return self.get_response(request)
