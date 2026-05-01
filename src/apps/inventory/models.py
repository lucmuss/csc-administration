from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Min, Max, Avg
from django.db.models.functions import Coalesce


class Strain(models.Model):
    PRODUCT_TYPE_FLOWER = "flower"
    PRODUCT_TYPE_CUTTING = "cutting"
    PRODUCT_TYPE_EDIBLE = "edible"
    PRODUCT_TYPE_ACCESSORY = "accessory"
    PRODUCT_TYPE_MERCH = "merch"
    PRODUCT_TYPE_CHOICES = [
        (PRODUCT_TYPE_FLOWER, "Bluete"),
        (PRODUCT_TYPE_CUTTING, "Steckling"),
        (PRODUCT_TYPE_EDIBLE, "Edible"),
        (PRODUCT_TYPE_ACCESSORY, "Rauchzubehoer"),
        (PRODUCT_TYPE_MERCH, "Werbegeschenk"),
    ]

    CARD_TONE_APRICOT = "apricot"
    CARD_TONE_MINT = "mint"
    CARD_TONE_SKY = "sky"
    CARD_TONE_LILAC = "lilac"
    CARD_TONE_SAND = "sand"
    CARD_TONE_BLUSH = "blush"
    CARD_TONE_CHOICES = [
        (CARD_TONE_APRICOT, "Apricot"),
        (CARD_TONE_MINT, "Mint"),
        (CARD_TONE_SKY, "Sky"),
        (CARD_TONE_LILAC, "Lilac"),
        (CARD_TONE_SAND, "Sand"),
        (CARD_TONE_BLUSH, "Blush"),
    ]

    QUALITY_A_PLUS = "A+"
    QUALITY_A = "A"
    QUALITY_B = "B"
    QUALITY_C = "C"
    QUALITY_CHOICES = [
        (QUALITY_A_PLUS, "A+"),
        (QUALITY_A, "A"),
        (QUALITY_B, "B"),
        (QUALITY_C, "C"),
    ]

    social_club = models.ForeignKey("core.SocialClub", on_delete=models.CASCADE, related_name="strains", null=True, blank=True)
    name = models.CharField(max_length=120)
    thc = models.DecimalField(max_digits=5, decimal_places=2)
    cbd = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    cbg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cbn = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cbc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cbv = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.DecimalField(max_digits=10, decimal_places=2)
    product_type = models.CharField(max_length=16, choices=PRODUCT_TYPE_CHOICES, default=PRODUCT_TYPE_FLOWER)
    card_tone = models.CharField(max_length=16, choices=CARD_TONE_CHOICES, default=CARD_TONE_APRICOT)
    quality_grade = models.CharField(max_length=2, choices=QUALITY_CHOICES, default=QUALITY_B)
    image = models.FileField(upload_to="strains/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        kwargs.pop("slug", None)
        if "thc_content" in kwargs and "thc" not in kwargs:
            kwargs["thc"] = kwargs.pop("thc_content")
        if "cbd_content" in kwargs and "cbd" not in kwargs:
            kwargs["cbd"] = kwargs.pop("cbd_content")
        if "price_per_gram" in kwargs and "price" not in kwargs:
            kwargs["price"] = kwargs.pop("price_per_gram")
        # Avoid injecting stock during DB hydration where positional args already carry this field.
        if "stock" not in kwargs and not args:
            kwargs["stock"] = Decimal("1000.00")
        super().__init__(*args, **kwargs)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["social_club", "name"], name="uniq_strain_name_per_social_club"),
        ]

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return self.name.lower().replace(" ", "-")

    @slug.setter
    def slug(self, value):
        return None

    @property
    def thc_content(self):
        return self.thc

    @thc_content.setter
    def thc_content(self, value):
        self.thc = value

    @property
    def cbd_content(self):
        return self.cbd

    @cbd_content.setter
    def cbd_content(self, value):
        self.cbd = value

    @property
    def price_per_gram(self):
        return self.price

    @price_per_gram.setter
    def price_per_gram(self, value):
        self.price = value

    def save(self, *args, **kwargs):
        previous_club_id = None
        if self.pk:
            previous_club_id = Strain.objects.filter(pk=self.pk).values_list("social_club_id", flat=True).first()
        super().save(*args, **kwargs)
        if self.social_club_id:
            self._refresh_social_club_price_stats(self.social_club_id)
        if previous_club_id and previous_club_id != self.social_club_id:
            self._refresh_social_club_price_stats(previous_club_id)

    def delete(self, *args, **kwargs):
        club_id = self.social_club_id
        super().delete(*args, **kwargs)
        if club_id:
            self._refresh_social_club_price_stats(club_id)

    @staticmethod
    def _refresh_social_club_price_stats(club_id: int) -> None:
        from apps.core.models import SocialClub

        aggregates = (
            Strain.objects.filter(social_club_id=club_id, is_active=True)
            .aggregate(
                min_price=Coalesce(Min("price"), Decimal("0.00")),
                max_price=Coalesce(Max("price"), Decimal("0.00")),
                avg_price=Coalesce(Avg("price"), Decimal("0.00")),
            )
        )
        SocialClub.objects.filter(pk=club_id).update(
            min_strain_price=aggregates["min_price"],
            max_strain_price=aggregates["max_price"],
            avg_strain_price=aggregates["avg_price"],
        )

    def reserve(self, grams: Decimal) -> None:
        if grams <= 0:
            raise ValidationError("Menge muss > 0 sein")
        if grams > self.stock:
            raise ValidationError("Nicht genug Bestand")
        self.stock -= grams
        self.save(update_fields=["stock"])

    def release(self, grams: Decimal) -> None:
        if grams <= 0:
            raise ValidationError("Menge muss > 0 sein")
        self.stock += grams
        self.save(update_fields=["stock"])

    @property
    def is_weight_based(self) -> bool:
        return self.product_type == self.PRODUCT_TYPE_FLOWER

    @property
    def unit_label(self) -> str:
        return "g" if self.is_weight_based else "Stk."

    @property
    def unit_price_label(self) -> str:
        return "pro Gramm" if self.is_weight_based else "pro Stueck"

    @property
    def stock_display(self) -> str:
        return f"{self.stock} {self.unit_label}"

    @property
    def card_palette(self) -> dict[str, str]:
        palettes = {
            self.CARD_TONE_APRICOT: {
                "background": "#fff3eb",
                "border": "#fdba74",
                "badge": "#ffedd5",
                "badge_text": "#9a3412",
            },
            self.CARD_TONE_MINT: {
                "background": "#effcf6",
                "border": "#86efac",
                "badge": "#dcfce7",
                "badge_text": "#166534",
            },
            self.CARD_TONE_SKY: {
                "background": "#eff6ff",
                "border": "#93c5fd",
                "badge": "#dbeafe",
                "badge_text": "#1d4ed8",
            },
            self.CARD_TONE_LILAC: {
                "background": "#f5f3ff",
                "border": "#c4b5fd",
                "badge": "#ede9fe",
                "badge_text": "#6d28d9",
            },
            self.CARD_TONE_SAND: {
                "background": "#fdf8f1",
                "border": "#fcd34d",
                "badge": "#fef3c7",
                "badge_text": "#92400e",
            },
            self.CARD_TONE_BLUSH: {
                "background": "#fff1f2",
                "border": "#fda4af",
                "badge": "#ffe4e6",
                "badge_text": "#be123c",
            },
        }
        return palettes.get(self.card_tone, palettes[self.CARD_TONE_APRICOT])


class InventoryLocation(models.Model):
    TYPE_DRY_ROOM = "dry_room"
    TYPE_VAULT = "vault"
    TYPE_SHELF = "shelf"
    TYPE_CHOICES = [
        (TYPE_DRY_ROOM, "Trockenraum"),
        (TYPE_VAULT, "Tresor"),
        (TYPE_SHELF, "Regal"),
    ]

    name = models.CharField(max_length=120, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SHELF)
    capacity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    strain = models.ForeignKey(Strain, on_delete=models.PROTECT, related_name="inventory_items")
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name="items")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    last_counted = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["location__name", "strain__name"]
        unique_together = ("strain", "location")

    def __str__(self):
        return f"{self.strain.name} @ {self.location.name}"


class InventoryCount(models.Model):
    date = models.DateField()
    items_counted = models.PositiveIntegerField(default=0)
    discrepancies = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Inventur {self.date}"


class _BatchCompatManager(models.Manager):
    @staticmethod
    def _normalize(kwargs: dict):
        data = dict(kwargs)
        if "batch_number" in data and "code" not in data:
            data["code"] = data.pop("batch_number")
        if "harvest_date" in data and "harvested_at" not in data:
            data["harvested_at"] = data.pop("harvest_date")
        if "available_grams" in data and "quantity" not in data:
            data["quantity"] = data.pop("available_grams")
        elif "total_harvested_grams" in data and "quantity" not in data:
            data["quantity"] = data.pop("total_harvested_grams")
        data.pop("price_per_gram", None)
        data.pop("status", None)
        data.pop("thc_content_actual", None)
        return data

    def create(self, **kwargs):
        return super().create(**self._normalize(kwargs))

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._normalize(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._normalize(kwargs))


class Batch(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_SOLD_OUT = "sold_out"
    STATUS_ARCHIVED = "archived"

    strain = models.ForeignKey(Strain, on_delete=models.PROTECT, related_name="batches")
    code = models.CharField(max_length=64, unique=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    harvested_at = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = _BatchCompatManager()

    def __init__(self, *args, **kwargs):
        legacy_status = kwargs.pop("status", None)
        if "batch_number" in kwargs and "code" not in kwargs:
            kwargs["code"] = kwargs.pop("batch_number")
        if "harvest_date" in kwargs and "harvested_at" not in kwargs:
            kwargs["harvested_at"] = kwargs.pop("harvest_date")
        if "available_grams" in kwargs and "quantity" not in kwargs:
            kwargs["quantity"] = kwargs.pop("available_grams")
        elif "total_harvested_grams" in kwargs and "quantity" not in kwargs:
            kwargs["quantity"] = kwargs.pop("total_harvested_grams")
        kwargs.pop("price_per_gram", None)
        super().__init__(*args, **kwargs)
        if legacy_status == self.STATUS_ARCHIVED:
            self.is_active = False

    class Meta:
        ordering = ["-created_at", "id"]
        verbose_name = "Charge"
        verbose_name_plural = "Chargen"

    def __str__(self):
        return self.code

    @property
    def batch_number(self):
        return self.code

    @batch_number.setter
    def batch_number(self, value):
        self.code = value

    @property
    def harvest_date(self):
        return self.harvested_at

    @harvest_date.setter
    def harvest_date(self, value):
        self.harvested_at = value

    @property
    def available_grams(self):
        return self.quantity

    @available_grams.setter
    def available_grams(self, value):
        self.quantity = value

    @property
    def total_harvested_grams(self):
        return self.quantity

    @total_harvested_grams.setter
    def total_harvested_grams(self, value):
        self.quantity = value

    @property
    def price_per_gram(self):
        return self.strain.price

    @property
    def thc_content_actual(self):
        return self.strain.thc

    @property
    def reserved_grams(self):
        return self.order_items.filter(order__status="reserved").aggregate(total=Coalesce(models.Sum("quantity_grams"), Decimal("0.00")))[
            "total"
        ] or Decimal("0.00")

    @property
    def status(self):
        if not self.is_active:
            return self.STATUS_ARCHIVED
        if self.quantity <= 0:
            return self.STATUS_SOLD_OUT
        return self.STATUS_AVAILABLE

    def update_status(self):
        # Legacy behavior: sold-out batches remain active records and only change computed status.
        self.is_active = True
        self.save(update_fields=["is_active"])
        return self.status


class InventoryTransaction(models.Model):
    KIND_RESERVATION = "reservation"
    KIND_RELEASE = "release"
    KIND_SALE = "sale"
    KIND_CHOICES = [
        (KIND_RESERVATION, "Reservierung"),
        (KIND_RELEASE, "Freigabe"),
        (KIND_SALE, "Verkauf"),
    ]

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="inventory_transactions")
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_transactions")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_RESERVATION)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.batch.code} {self.kind} {self.quantity}"
