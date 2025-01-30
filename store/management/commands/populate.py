# store/management(commands/populate.py)

from django.core.management.base import BaseCommand
from store.models import Status, Order, OrderItem
import random

class Command(BaseCommand):
    help = 'Populate database with test data'

    def handle(self, *args, **options):
        # Delete all
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Status.objects.all().delete()

        # Create all Status
        status0, created = Status.objects.get_or_create(name='No pagado')
        status1, created = Status.objects.get_or_create(name='Aceptado')
        status2, created = Status.objects.get_or_create(name='Denegado')  
        status3, created = Status.objects.get_or_create(name='En trámite')
        status4, created = Status.objects.get_or_create(name='No realizado')     
