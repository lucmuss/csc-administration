from django.db import models


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
