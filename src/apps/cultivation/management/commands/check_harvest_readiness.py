from django.core.management.base import BaseCommand

from apps.cultivation.models import Plant
from apps.cultivation.services import HarvestService


class Command(BaseCommand):
    help = "Prueft naechste Erntereife fuer aktive Pflanzen"

    def handle(self, *args, **options):
        plants = Plant.objects.exclude(growth_stage=Plant.STAGE_HARVESTED)
        if not plants.exists():
            self.stdout.write("Keine aktiven Pflanzen vorhanden")
            return

        for plant in plants:
            eta = HarvestService.estimate_harvest_date(plant=plant)
            self.stdout.write(f"Pflanze #{plant.id} ({plant.cutting.mother_plant.strain.name}) -> Prognose: {eta}")
