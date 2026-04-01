from django.db import models


class ClubConfiguration(models.Model):
    app_name = models.CharField(max_length=120, blank=True)
    app_tagline = models.CharField(max_length=160, blank=True)
    app_description = models.TextField(blank=True)
    club_name = models.CharField(max_length=180, blank=True)
    club_slogan = models.CharField(max_length=180, blank=True)
    club_contact_email = models.EmailField(blank=True)
    club_support_email = models.EmailField(blank=True)
    club_contact_phone = models.CharField(max_length=80, blank=True)
    club_contact_address = models.TextField(blank=True)
    club_board_representatives = models.TextField(blank=True)
    club_register_entry = models.CharField(max_length=180, blank=True)
    club_register_court = models.CharField(max_length=180, blank=True)
    club_tax_number = models.CharField(max_length=180, blank=True)
    club_vat_id = models.CharField(max_length=180, blank=True)
    club_supervisory_authority = models.CharField(max_length=180, blank=True)
    club_content_responsible = models.CharField(max_length=180, blank=True)
    club_responsible_person = models.TextField(blank=True)
    club_membership_email = models.EmailField(blank=True)
    club_prevention_email = models.EmailField(blank=True)
    club_finance_email = models.EmailField(blank=True)
    club_privacy_contact = models.EmailField(blank=True)
    club_data_protection_officer = models.CharField(max_length=180, blank=True)
    club_language_notice = models.TextField(blank=True)
    club_legal_basis_notice = models.TextField(blank=True)
    club_retention_notice = models.TextField(blank=True)
    club_external_services_text = models.TextField(blank=True)
    prevention_officer_name = models.CharField(max_length=180, blank=True)
    prevention_notice = models.TextField(blank=True)
    instagram_url = models.URLField(blank=True)
    email_signature_text = models.TextField(blank=True)
    email_signature_html = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Club-Konfiguration"
        verbose_name_plural = "Club-Konfiguration"

    def __str__(self):
        return self.club_name or self.app_name or "Club-Konfiguration"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)


class PublicDocument(models.Model):
    CATEGORY_STATUTE = "statute"
    CATEGORY_POLICY = "policy"
    CATEGORY_INFO = "info"
    CATEGORY_FORM = "form"
    CATEGORY_OTHER = "other"
    CATEGORY_CHOICES = [
        (CATEGORY_STATUTE, "Satzung"),
        (CATEGORY_POLICY, "Ordnung / Richtlinie"),
        (CATEGORY_INFO, "Information"),
        (CATEGORY_FORM, "Formular"),
        (CATEGORY_OTHER, "Sonstiges"),
    ]

    title = models.CharField(max_length=160)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="documents/")
    is_public = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "title", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def file_extension(self) -> str:
        name = getattr(self.file, "name", "") or ""
        if "." not in name:
            return ""
        return name.rsplit(".", 1)[-1].lower()

    @property
    def file_badge(self) -> str:
        extension = self.file_extension
        if not extension:
            return "Datei"
        return extension.upper()

    @property
    def file_action_label(self) -> str:
        extension = self.file_extension
        if extension == "pdf":
            return "PDF herunterladen"
        if extension in {"jpg", "jpeg", "png", "webp", "gif"}:
            return "Datei ansehen"
        return "Datei herunterladen"
