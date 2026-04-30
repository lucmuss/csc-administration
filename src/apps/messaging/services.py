# messaging/services.py
"""Messaging helper services."""
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from django.conf import settings
from .models import EmailGroup, EmailGroupMember, SmsProviderConfig, SmsMessage


IMPORTANT_EMAIL_GROUP = "Wichtige Vereinsinfos"
MARKETING_EMAIL_GROUP = "Preislisten und Angebote"


def _ensure_email_group(name: str, description: str):
    group, _ = EmailGroup.objects.get_or_create(
        name=name,
        defaults={"description": description, "is_active": True},
    )
    if not group.is_active:
        group.is_active = True
        group.save(update_fields=["is_active", "updated_at"])
    return group


def sync_member_messaging_preferences(profile) -> None:
    """Synchronisiert Profil-Opt-ins in die E-Mail-Gruppen."""
    if not getattr(profile, "pk", None):
        return

    status = getattr(profile, "status", "")
    is_verified = bool(getattr(profile, "is_verified", False))
    receives_club_updates = status in {"active", "verified"} or is_verified

    important_group = _ensure_email_group(
        IMPORTANT_EMAIL_GROUP,
        "Pflichtkommunikation fuer organisatorische Vereinsinformationen.",
    )
    marketing_group = _ensure_email_group(
        MARKETING_EMAIL_GROUP,
        "Optionale Preislisten, Angebots- und Verfuegbarkeitsmails.",
    )

    memberships = [
        (important_group, receives_club_updates),
        (marketing_group, bool(profile.optional_newsletter_opt_in)),
    ]
    for group, should_be_member in memberships:
        if should_be_member:
            EmailGroupMember.objects.get_or_create(
                group=group,
                member=profile,
                defaults={"added_by": None},
            )
        else:
            EmailGroupMember.objects.filter(group=group, member=profile).delete()


class SmsService(ABC):
    """Basis-Service für SMS-Versand"""
    
    def __init__(self, provider: SmsProviderConfig):
        self.provider = provider
    
    @abstractmethod
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """Sendet eine SMS."""
    
    @abstractmethod
    def get_status(self, external_id: str) -> Dict[str, Any]:
        """Holt den Status einer gesendeten SMS."""


class TwilioService(SmsService):
    """Twilio SMS Service"""
    
    BASE_URL = "https://api.twilio.com/2010-04-01"
    
    def __init__(self, provider: SmsProviderConfig):
        super().__init__(provider)
        self.account_sid = provider.api_key
        self.auth_token = provider.api_secret
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """Sendet eine SMS über Twilio"""
        import requests
        url = f"{self.BASE_URL}/Accounts/{self.account_sid}/Messages.json"
        
        payload = {
            "To": to,
            "From": self.provider.sender_number,
            "Body": message
        }
        
        try:
            response = requests.post(
                url,
                data=payload,
                auth=(self.account_sid, self.auth_token),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "external_id": data.get("sid"),
                "status": data.get("status", "queued"),
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": getattr(e.response, "text", None) if hasattr(e, "response") else None
            }
    
    def get_status(self, external_id: str) -> Dict[str, Any]:
        """Holt den Status einer Twilio SMS"""
        import requests
        url = f"{self.BASE_URL}/Accounts/{self.account_sid}/Messages/{external_id}.json"
        
        try:
            response = requests.get(url, auth=(self.account_sid, self.auth_token), timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "status": data.get("status"),
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }


class VonageService(SmsService):
    """Vonage (ehemals Nexmo) SMS Service"""
    
    BASE_URL = "https://rest.nexmo.com/sms/json"
    
    def __init__(self, provider: SmsProviderConfig):
        super().__init__(provider)
        self.api_key = provider.api_key
        self.api_secret = provider.api_secret
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """Sendet eine SMS über Vonage"""
        import requests
        payload = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "from": self.provider.sender_number,
            "to": to,
            "text": message
        }
        
        try:
            response = requests.post(self.BASE_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            messages = data.get("messages", [])
            if messages and messages[0].get("status") == "0":
                return {
                    "success": True,
                    "external_id": messages[0].get("message-id"),
                    "status": "queued",
                    "raw_response": data
                }
            else:
                error_text = messages[0].get("error-text", "Unknown error") if messages else "Unknown error"
                return {
                    "success": False,
                    "error": error_text,
                    "raw_response": data
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_status(self, external_id: str) -> Dict[str, Any]:
        """Vonage unterstützt keinen direkten Status-Check"""
        return {
            "success": False,
            "error": "Status-Check nicht unterstützt"
        }


class CustomWebhookService(SmsService):
    """Custom Webhook SMS Service"""
    
    def __init__(self, provider: SmsProviderConfig):
        super().__init__(provider)
        self.webhook_url = provider.webhook_url
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """Sendet eine SMS über Custom Webhook"""
        import requests
        payload = {
            "to": to,
            "from": self.provider.sender_number,
            "message": message,
            "api_key": self.provider.api_key
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.provider.api_secret}" if self.provider.api_secret else None
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={k: v for k, v in headers.items() if v},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": data.get("success", True),
                "external_id": data.get("id"),
                "status": data.get("status", "queued"),
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": getattr(e.response, "text", None) if hasattr(e, "response") else None
            }
    
    def get_status(self, external_id: str) -> Dict[str, Any]:
        """Status-Check über Custom Webhook"""
        import requests
        # Annahme: Webhook unterstützt GET für Status
        url = f"{self.webhook_url}/status/{external_id}"
        
        try:
            headers = {}
            if self.provider.api_secret:
                headers["Authorization"] = f"Bearer {self.provider.api_secret}"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "status": data.get("status"),
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }


def get_sms_service(provider: SmsProviderConfig) -> SmsService:
    """Factory-Funktion für SMS Services"""
    if provider.provider == "twilio":
        return TwilioService(provider)
    elif provider.provider == "vonage":
        return VonageService(provider)
    elif provider.provider == "custom":
        return CustomWebhookService(provider)
    else:
        raise ValueError(f"Unbekannter Provider: {provider.provider}")


def send_sms_message(sms_message: SmsMessage) -> bool:
    """Sendet eine SMS-Nachricht über den konfigurierten Provider"""
    if not sms_message.provider:
        sms_message.status = "failed"
        sms_message.error_message = "Kein Provider konfiguriert"
        sms_message.save()
        return False
    
    service = get_sms_service(sms_message.provider)
    
    # Bestimme Empfängernummer
    if sms_message.recipient_member:
        # Versuche Telefonnummer aus Profil zu holen
        # Annahme: Profil hat phone-Feld oder wir nutzen eine andere Quelle
        to_number = getattr(sms_message.recipient_member, "phone", None)
        if not to_number:
            to_number = sms_message.recipient_phone
    else:
        to_number = sms_message.recipient_phone
    
    if not to_number:
        sms_message.status = "failed"
        sms_message.error_message = "Keine Empfängernummer"
        sms_message.save()
        return False
    
    # Sende SMS
    result = service.send_sms(to_number, sms_message.content)
    
    if result["success"]:
        sms_message.status = "sent"
        sms_message.external_id = result.get("external_id", "")
        sms_message.cost = sms_message.provider.cost_per_sms * sms_message.sms_count
        from django.utils import timezone
        sms_message.sent_at = timezone.now()
    else:
        sms_message.status = "failed"
        sms_message.error_message = result.get("error", "Unbekannter Fehler")
    
    sms_message.save()
    return result["success"]


def normalize_phone_number(phone: str) -> str:
    """Normalisiert eine Telefonnummer für den internationalen Versand"""
    # Entferne Leerzeichen und andere Zeichen
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Füge + hinzu wenn nicht vorhanden
    if not phone.startswith("+"):
        if phone.startswith("00"):
            phone = "+" + phone[2:]
        elif phone.startswith("0"):
            # Deutsche Nummer - füge +49 hinzu
            phone = "+49" + phone[1:]
    
    return phone
