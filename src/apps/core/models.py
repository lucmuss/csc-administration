from decimal import Decimal

from django.db import models
from django.utils.text import slugify


class SocialClub(models.Model):
    BUNDESLAND_BW = "BW"
    BUNDESLAND_BY = "BY"
    BUNDESLAND_BE = "BE"
    BUNDESLAND_BB = "BB"
    BUNDESLAND_HB = "HB"
    BUNDESLAND_HH = "HH"
    BUNDESLAND_HE = "HE"
    BUNDESLAND_MV = "MV"
    BUNDESLAND_NI = "NI"
    BUNDESLAND_NW = "NW"
    BUNDESLAND_RP = "RP"
    BUNDESLAND_SL = "SL"
    BUNDESLAND_SN = "SN"
    BUNDESLAND_ST = "ST"
    BUNDESLAND_SH = "SH"
    BUNDESLAND_TH = "TH"
    FEDERAL_STATE_CHOICES = [
        (BUNDESLAND_BW, "Baden-Wuerttemberg"),
        (BUNDESLAND_BY, "Bayern"),
        (BUNDESLAND_BE, "Berlin"),
        (BUNDESLAND_BB, "Brandenburg"),
        (BUNDESLAND_HB, "Bremen"),
        (BUNDESLAND_HH, "Hamburg"),
        (BUNDESLAND_HE, "Hessen"),
        (BUNDESLAND_MV, "Mecklenburg-Vorpommern"),
        (BUNDESLAND_NI, "Niedersachsen"),
        (BUNDESLAND_NW, "Nordrhein-Westfalen"),
        (BUNDESLAND_RP, "Rheinland-Pfalz"),
        (BUNDESLAND_SL, "Saarland"),
        (BUNDESLAND_SN, "Sachsen"),
        (BUNDESLAND_ST, "Sachsen-Anhalt"),
        (BUNDESLAND_SH, "Schleswig-Holstein"),
        (BUNDESLAND_TH, "Thueringen"),
    ]

    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    public_description = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="social_clubs/profile/", blank=True)
    banner_image = models.ImageField(upload_to="social_clubs/banner/", blank=True)
    gallery_image_1 = models.ImageField(upload_to="social_clubs/gallery/", blank=True)
    gallery_image_2 = models.ImageField(upload_to="social_clubs/gallery/", blank=True)
    gallery_image_3 = models.ImageField(upload_to="social_clubs/gallery/", blank=True)
    gallery_image_4 = models.ImageField(upload_to="social_clubs/gallery/", blank=True)
    gallery_image_5 = models.ImageField(upload_to="social_clubs/gallery/", blank=True)
    email = models.EmailField()
    street_address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=120)
    federal_state = models.CharField(max_length=2, choices=FEDERAL_STATE_CHOICES, blank=True)
    minimum_age = models.PositiveSmallIntegerField(default=21)
    max_verified_members = models.PositiveIntegerField(default=500)
    admission_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    monthly_membership_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("24.00"))
    avg_strain_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    min_strain_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    max_strain_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    club_iban = models.CharField(max_length=34, blank=True)
    club_bic = models.CharField(max_length=11, blank=True)
    stripe_account_id = models.CharField(max_length=128, blank=True)
    stripe_dashboard_url = models.URLField(blank=True)
    phone = models.CharField(max_length=32)
    website = models.URLField(blank=True)
    support_email = models.EmailField(blank=True)
    membership_email = models.EmailField(blank=True)
    prevention_email = models.EmailField(blank=True)
    finance_email = models.EmailField(blank=True)
    privacy_contact = models.EmailField(blank=True)
    data_protection_officer = models.CharField(max_length=180, blank=True)
    board_representatives = models.TextField(blank=True)
    register_entry = models.CharField(max_length=180, blank=True)
    register_court = models.CharField(max_length=180, blank=True)
    tax_number = models.CharField(max_length=180, blank=True)
    vat_id = models.CharField(max_length=180, blank=True)
    supervisory_authority = models.CharField(max_length=180, blank=True)
    content_responsible = models.CharField(max_length=180, blank=True)
    responsible_person = models.TextField(blank=True)
    language_notice = models.TextField(blank=True)
    legal_basis_notice = models.TextField(blank=True)
    retention_notice = models.TextField(blank=True)
    external_services_text = models.TextField(blank=True)
    prevention_officer_name = models.CharField(max_length=180, blank=True)
    prevention_notice = models.TextField(blank=True)
    instagram_url = models.URLField(blank=True)
    telegram_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def gallery_images(self):
        return [
            self.gallery_image_1,
            self.gallery_image_2,
            self.gallery_image_3,
            self.gallery_image_4,
            self.gallery_image_5,
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:200] or "social-club"
            candidate = base
            suffix = 2
            while SocialClub.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class SocialClubOpeningHour(models.Model):
    WEEKDAY_MONDAY = 0
    WEEKDAY_TUESDAY = 1
    WEEKDAY_WEDNESDAY = 2
    WEEKDAY_THURSDAY = 3
    WEEKDAY_FRIDAY = 4
    WEEKDAY_SATURDAY = 5
    WEEKDAY_SUNDAY = 6
    WEEKDAY_CHOICES = [
        (WEEKDAY_MONDAY, "Montag"),
        (WEEKDAY_TUESDAY, "Dienstag"),
        (WEEKDAY_WEDNESDAY, "Mittwoch"),
        (WEEKDAY_THURSDAY, "Donnerstag"),
        (WEEKDAY_FRIDAY, "Freitag"),
        (WEEKDAY_SATURDAY, "Samstag"),
        (WEEKDAY_SUNDAY, "Sonntag"),
    ]

    social_club = models.ForeignKey(SocialClub, on_delete=models.CASCADE, related_name="opening_hours")
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    starts_at = models.TimeField()
    ends_at = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["weekday", "starts_at", "ends_at", "id"]

    def __str__(self):
        return f"{self.social_club.name} · {self.get_weekday_display()} {self.starts_at}-{self.ends_at}"


class ClubConfiguration(models.Model):
    app_name = models.CharField(max_length=120, blank=True)
    app_tagline = models.CharField(max_length=160, blank=True)
    app_description = models.TextField(blank=True)
    club_name = models.CharField(max_length=180, blank=True)
    club_slogan = models.CharField(max_length=180, blank=True)
    club_contact_email = models.EmailField(blank=True)
    club_support_email = models.EmailField(blank=True)
    club_contact_phone = models.CharField(max_length=80, blank=True)
    telegram_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)
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
    social_club = models.ForeignKey(SocialClub, on_delete=models.CASCADE, related_name="documents", null=True, blank=True)
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


class SocialClubReview(models.Model):
    social_club = models.ForeignKey(SocialClub, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="social_club_reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["social_club", "user"], name="unique_social_club_review_per_user"),
            models.CheckConstraint(check=models.Q(rating__gte=1) & models.Q(rating__lte=5), name="social_club_review_rating_1_5"),
        ]

    def __str__(self):
        return f"{self.social_club.name} · {self.user.email} ({self.rating}/5)"
