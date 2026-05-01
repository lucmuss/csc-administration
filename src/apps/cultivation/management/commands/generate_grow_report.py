from django.core.management.base import BaseCommand

from apps.cultivation.models import GrowCycle, HarvestBatch, Plant, PlantLog


class Command(BaseCommand):
    help = "Erzeugt einen kompakten Anbau-Bericht"

    def handle(self, *args, **options):
        self.stdout.write("CSC Anbau-Bericht")
        self.stdout.write(f"Grow Cycles: {GrowCycle.objects.count()}")
        self.stdout.write(f"Aktive Pflanzen: {Plant.objects.exclude(status__in=[Plant.STATUS_HARVESTED, Plant.STATUS_COMPLETED, Plant.STATUS_DEAD]).count()}")
        self.stdout.write(f"Ernten: {HarvestBatch.objects.count()}")
        self.stdout.write(f"Growtagebuch-Eintraege: {PlantLog.objects.count()}")
