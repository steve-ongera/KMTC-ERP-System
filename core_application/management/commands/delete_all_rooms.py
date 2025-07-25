from django.core.management.base import BaseCommand
from coreapplication.models import HostelRoom

class Command(BaseCommand):
    help = 'Delete all hostel rooms and their related beds'

    def handle(self, *args, **kwargs):
        count = HostelRoom.objects.count()
        HostelRoom.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} hostel rooms and their beds.'))
