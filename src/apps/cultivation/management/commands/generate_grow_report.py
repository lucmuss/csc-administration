from django.core.management.base import BaseCommand

from apps.cultivation.models import GrowthLog, Harvest, MotherPlant, Plant


class Command(BaseCommand):
    help = "Erzeugt einen kompakten Anbau-Bericht"

    def handle(self, *args, **options):
        self.stdout.write("CSC Anbau-Bericht")
        self.stdout.write(f"Mutterpflanzen: {MotherPlant.objects.count()}")
        self.stdout.write(f"Aktive Pflanzen: {Plant.objects.exclude(growth_stage=Plant.STAGE_HARVESTED).count()}")
        self.stdout.write(f"Ernten: {Harvest.objects.count()}")
        self.stdout.write(f"Growtagebuch-Eintraege: {GrowthLog.objects.count()}")
