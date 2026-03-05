# config/context_processors.py
from django.conf import settings


def ga_tracking_id(request):
    """Fuegt Google Analytics Tracking ID zum Template Context hinzu"""
    return {
        "ga_tracking_id": getattr(settings, "GA_TRACKING_ID", ""),
    }
