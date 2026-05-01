from django.core.management.base import BaseCommand

from apps.cultivation.models import Plant


class Command(BaseCommand):
    help = "Prueft naechste Erntereife fuer aktive Pflanzen"

    def handle(self, *args, **options):
        plants = Plant.objects.select_related("grow_cycle", "strain").exclude(
            status__in=[Plant.STATUS_HARVESTED, Plant.STATUS_COMPLETED, Plant.STATUS_DEAD]
        )
        if not plants.exists():
            self.stdout.write("Keine aktiven Pflanzen vorhanden")
            return

        for plant in plants:
            eta = plant.grow_cycle.expected_harvest_date
            self.stdout.write(f"Pflanze #{plant.id} ({plant.strain.name}) -> Prognose: {eta}")
