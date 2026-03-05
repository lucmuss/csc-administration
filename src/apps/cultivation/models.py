# cultivation/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from apps.members.models import Profile
from apps.inventory.models import Strain

User = get_user_model()


class GrowCycle(models.Model):
    """Anbau-Zyklus (Grow Cycle)"""
    
    STATUS_PLANNED = "planned"
    STATUS_ACTIVE = "active"
    STATUS_HARVESTED = "harvested"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PLANNED, "Geplant"),
        (STATUS_ACTIVE, "Aktiv"),
        (STATUS_HARVESTED, "Geerntet"),
        (STATUS_COMPLETED, "Abgeschlossen"),
        (STATUS_CANCELLED, "Abgebrochen"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    
    # Zeitraum
    start_date = models.DateField(verbose_name="Startdatum")
    expected_harvest_date = models.DateField(verbose_name="Erwartetes Erntedatum")
    actual_harvest_date = models.DateField(null=True, blank=True, verbose_name="Tatsächliches Erntedatum")
    completion_date = models.DateField(null=True, blank=True, verbose_name="Abschlussdatum")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PLANNED,
        verbose_name="Status"
    )
    
    # Verantwortung
    responsible_member = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grow_cycles",
        verbose_name="Verantwortliches Mitglied"
    )
    
    # Standort
    location = models.CharField(max_length=200, blank=True, verbose_name="Standort")
    
    # Notizen
    notes = models.TextField(blank=True, verbose_name="Notizen")
    
    # Compliance
    compliance_notes = models.TextField(blank=True, verbose_name="Compliance-Notizen (CanG)")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_grow_cycles"
    )
    
    class Meta:
        verbose_name = "Grow Cycle"
        verbose_name_plural = "Grow Cycles"
        ordering = ["-start_date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "start_date"]),
            models.Index(fields=["responsible_member", "status"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def plant_count(self):
        return self.plants.count()
    
    @property
    def days_active(self):
        """Berechnet die Anzahl der aktiven Tage"""
        from datetime import date
        if self.status == self.STATUS_PLANNED:
            return 0
        end_date = self.actual_harvest_date or date.today()
        return (end_date - self.start_date).days
    
    @property
    def days_until_harvest(self):
        """Berechnet die Tage bis zur erwarteten Ernte"""
        from datetime import date
        if self.status in [self.STATUS_HARVESTED, self.STATUS_COMPLETED, self.STATUS_CANCELLED]:
            return 0
        return (self.expected_harvest_date - date.today()).days
    
    @property
    def total_expected_yield(self):
        """Berechnet den erwarteten Gesamtertrag"""
        return self.plants.aggregate(
            total=models.Sum("expected_yield_grams")
        )["total"] or Decimal("0")
    
    @property
    def total_actual_yield(self):
        """Berechnet den tatsächlichen Gesamtertrag"""
        return self.plants.aggregate(
            total=models.Sum("actual_yield_grams")
        )["total"] or Decimal("0")


class Plant(models.Model):
    """Einzelne Pflanze"""
    
    STATUS_GROWING = "growing"
    STATUS_VEGETATIVE = "vegetative"
    STATUS_FLOWERING = "flowering"
    STATUS_HARVESTED = "harvested"
    STATUS_DRYING = "drying"
    STATUS_CURING = "curing"
    STATUS_COMPLETED = "completed"
    STATUS_DEAD = "dead"
    STATUS_CHOICES = [
        (STATUS_GROWING, "Wachsend"),
        (STATUS_VEGETATIVE, "Vegetativ"),
        (STATUS_FLOWERING, "Blüte"),
        (STATUS_HARVESTED, "Geerntet"),
        (STATUS_DRYING, "Trocknend"),
        (STATUS_CURING, "Aushärtend"),
        (STATUS_COMPLETED, "Abgeschlossen"),
        (STATUS_DEAD, "Abgestorben"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Zuordnung
    grow_cycle = models.ForeignKey(
        GrowCycle,
        on_delete=models.CASCADE,
        related_name="plants",
        verbose_name="Grow Cycle"
    )
    strain = models.ForeignKey(
        Strain,
        on_delete=models.PROTECT,
        related_name="plants",
        verbose_name="Strain"
    )
    
    # Identifikation
    plant_number = models.CharField(max_length=20, blank=True, verbose_name="Pflanzen-Nummer")
    qr_code_id = models.CharField(max_length=100, unique=True, blank=True, verbose_name="QR-Code ID")
    
    # Zeitraum
    planting_date = models.DateField(verbose_name="Pflanzdatum")
    harvest_date = models.DateField(null=True, blank=True, verbose_name="Erntedatum")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_GROWING,
        verbose_name="Status"
    )
    
    # Ertrag
    expected_yield_grams = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Erwarteter Ertrag (g)"
    )
    actual_yield_grams = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Tatsächlicher Ertrag (g)"
    )
    
    # Notizen
    notes = models.TextField(blank=True, verbose_name="Notizen")
    
    # Compliance
    compliance_notes = models.TextField(blank=True, verbose_name="Compliance-Notizen (CanG)")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_plants"
    )
    
    class Meta:
        verbose_name = "Pflanze"
        verbose_name_plural = "Pflanzen"
        ordering = ["grow_cycle", "plant_number", "created_at"]
        indexes = [
            models.Index(fields=["grow_cycle", "status"]),
            models.Index(fields=["strain", "status"]),
            models.Index(fields=["qr_code_id"]),
        ]
    
    def __str__(self):
        if self.plant_number:
            return f"Pflanze #{self.plant_number} ({self.strain.name})"
        return f"Pflanze {self.id.hex[:8]} ({self.strain.name})"
    
    def save(self, *args, **kwargs):
        # Generiere QR-Code ID falls nicht vorhanden
        if not self.qr_code_id:
            self.qr_code_id = f"PLANT-{self.id.hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def age_days(self):
        """Berechnet das Alter der Pflanze in Tagen"""
        from datetime import date
        return (date.today() - self.planting_date).days
    
    @property
    def is_active(self):
        """Prüft ob die Pflanze noch aktiv ist"""
        return self.status not in [self.STATUS_COMPLETED, self.STATUS_DEAD]
    
    @property
    def is_harvested(self):
        """Prüft ob die Pflanze geerntet wurde"""
        return self.status in [self.STATUS_HARVESTED, self.STATUS_DRYING, self.STATUS_CURING, self.STATUS_COMPLETED]


class PlantLog(models.Model):
    """Log-Eintrag für Pflanzenpflege"""
    
    LOG_TYPE_WATERING = "watering"
    LOG_TYPE_FERTILIZING = "fertilizing"
    LOG_TYPE_PRUNING = "pruning"
    LOG_TYPE_PEST_CONTROL = "pest_control"
    LOG_TYPE_TRANSPLANTING = "transplanting"
    LOG_TYPE_HARVEST = "harvest"
    LOG_TYPE_TRAINING = "training"
    LOG_TYPE_OBSERVATION = "observation"
    LOG_TYPE_OTHER = "other"
    LOG_TYPE_CHOICES = [
        (LOG_TYPE_WATERING, "Gießen"),
        (LOG_TYPE_FERTILIZING, "Düngen"),
        (LOG_TYPE_PRUNING, "Schneiden/Trimmen"),
        (LOG_TYPE_PEST_CONTROL, "Schädlingsbekämpfung"),
        (LOG_TYPE_TRANSPLANTING, "Umtopfen"),
        (LOG_TYPE_HARVEST, "Ernte"),
        (LOG_TYPE_TRAINING, "Training (LST/HST)"),
        (LOG_TYPE_OBSERVATION, "Beobachtung"),
        (LOG_TYPE_OTHER, "Sonstiges"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Zuordnung
    plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Pflanze"
    )
    
    # Log-Details
    log_type = models.CharField(
        max_length=20,
        choices=LOG_TYPE_CHOICES,
        verbose_name="Typ"
    )
    date = models.DateTimeField(verbose_name="Datum/Uhrzeit")
    
    # Details
    notes = models.TextField(blank=True, verbose_name="Notizen")
    products_used = models.TextField(blank=True, verbose_name="Verwendete Produkte")
    
    # Fotos (optional - als URL/Referenz)
    photo_url = models.URLField(blank=True, verbose_name="Foto URL")
    
    # Durchgeführt von
    performed_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plant_logs",
        verbose_name="Durchgeführt von"
    )
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_plant_logs"
    )
    
    class Meta:
        verbose_name = "Pflanzen-Log"
        verbose_name_plural = "Pflanzen-Logs"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["plant", "log_type", "date"]),
            models.Index(fields=["performed_by", "date"]),
        ]
    
    def __str__(self):
        return f"{self.get_log_type_display()} - {self.plant} ({self.date.strftime('%d.%m.%Y')})"


class HarvestBatch(models.Model):
    """Ernte-Batch für mehrere Pflanzen"""
    
    QUALITY_A_PLUS = "A+"
    QUALITY_A = "A"
    QUALITY_B = "B"
    QUALITY_C = "C"
    QUALITY_CHOICES = [
        (QUALITY_A_PLUS, "A+ (Premium)"),
        (QUALITY_A, "A (Hochwertig)"),
        (QUALITY_B, "B (Standard)"),
        (QUALITY_C, "C (Low)"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identifikation
    batch_number = models.CharField(max_length=50, unique=True, verbose_name="Batch-Nummer")
    name = models.CharField(max_length=100, blank=True, verbose_name="Bezeichnung")
    
    # Zeitraum
    harvest_date = models.DateField(verbose_name="Erntedatum")
    
    # Pflanzen
    plants = models.ManyToManyField(
        Plant,
        related_name="harvest_batches",
        verbose_name="Pflanzen"
    )
    
    # Gewichte
    total_weight_fresh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Frischgewicht (g)"
    )
    total_weight_dried = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Trockengewicht (g)"
    )
    
    # Qualität
    quality_grade = models.CharField(
        max_length=2,
        choices=QUALITY_CHOICES,
        default=QUALITY_A,
        verbose_name="Qualitätsstufe"
    )
    
    # Trocknung
    drying_start_date = models.DateField(null=True, blank=True, verbose_name="Trocknungsstart")
    drying_end_date = models.DateField(null=True, blank=True, verbose_name="Trocknungsende")
    
    # Aushärtung (Curing)
    curing_start_date = models.DateField(null=True, blank=True, verbose_name="Aushärtungsstart")
    curing_end_date = models.DateField(null=True, blank=True, verbose_name="Aushärtungsende")
    
    # Inventory-Zuweisung
    assigned_to_inventory = models.BooleanField(default=False, verbose_name="Dem Inventar zugewiesen")
    inventory_item = models.ForeignKey(
        "inventory.InventoryItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="harvest_batches",
        verbose_name="Inventar-Item"
    )
    
    # Notizen
    notes = models.TextField(blank=True, verbose_name="Notizen")
    
    # Compliance
    compliance_notes = models.TextField(blank=True, verbose_name="Compliance-Notizen (CanG)")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_harvest_batches"
    )
    
    class Meta:
        verbose_name = "Ernte-Batch"
        verbose_name_plural = "Ernte-Batches"
        ordering = ["-harvest_date", "-created_at"]
        indexes = [
            models.Index(fields=["harvest_date", "quality_grade"]),
            models.Index(fields=["assigned_to_inventory", "harvest_date"]),
        ]
    
    def __str__(self):
        if self.name:
            return f"{self.batch_number} - {self.name}"
        return self.batch_number
    
    def save(self, *args, **kwargs):
        # Generiere Batch-Nummer falls nicht vorhanden
        if not self.batch_number:
            from datetime import date
            today = date.today()
            count = HarvestBatch.objects.filter(
                harvest_date__year=today.year,
                harvest_date__month=today.month
            ).count() + 1
            self.batch_number = f"H-{today.strftime('%Y%m')}-{count:03d}"
        super().save(*args, **kwargs)
    
    @property
    def plant_count(self):
        return self.plants.count()
    
    @property
    def drying_loss_percentage(self):
        """Berechnet den Trocknungsverlust in Prozent"""
        if self.total_weight_fresh > 0:
            loss = self.total_weight_fresh - self.total_weight_dried
            return (loss / self.total_weight_fresh) * 100
        return Decimal("0.00")
    
    @property
    def is_ready_for_inventory(self):
        """Prüft ob der Batch dem Inventar zugewiesen werden kann"""
        return (
            self.total_weight_dried > 0 and
            self.curing_end_date is not None and
            not self.assigned_to_inventory
        )
    
    @property
    def strain_display(self):
        """Zeigt die Strains des Batches an"""
        strains = self.plants.values_list("strain__name", flat=True).distinct()
        return ", ".join(strains) if strains else "-"
