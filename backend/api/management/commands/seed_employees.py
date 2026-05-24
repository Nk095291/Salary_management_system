import random
import time

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Employee
from api.utils.management.commands.seed_employees import DATA_DIR, build_employee, load_names


class Command(BaseCommand):
    help = 'Seed employees using names from data/first_names.txt and data/last_names.txt.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10_000,
            help='Number of employees to create (default: 10000).',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='bulk_create batch size (default: 1000).',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing employees before seeding.',
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=42,
            help='Random seed for reproducible data (default: 42).',
        )

    def handle(self, *args, **options):
        count = options['count']
        batch_size = options['batch_size']
        clear = options['clear']
        rng = random.Random(options['seed'])

        if count <= 0:
            self.stderr.write(self.style.ERROR('Count must be greater than 0.'))
            return

        first_names_path = DATA_DIR / 'first_names.txt'
        last_names_path = DATA_DIR / 'last_names.txt'
        if not first_names_path.exists() or not last_names_path.exists():
            self.stderr.write(
                self.style.ERROR(
                    f'Name files required: {first_names_path} and {last_names_path}'
                )
            )
            return

        first_names = load_names(first_names_path)
        last_names = load_names(last_names_path)
        if not first_names or not last_names:
            self.stderr.write(self.style.ERROR('Name files must not be empty.'))
            return

        start = time.perf_counter()

        with transaction.atomic():
            if clear:
                deleted, _ = Employee.objects.all().delete()
                self.stdout.write(f'Cleared {deleted} existing employee(s).')

            created = 0
            batch: list[Employee] = []
            for index in range(count):
                batch.append(
                    build_employee(index + 1, first_names, last_names, rng)
                )
                if len(batch) >= batch_size:
                    Employee.objects.bulk_create(batch, batch_size=batch_size)
                    created += len(batch)
                    self.stdout.write(f'Created {created}/{count} employees...')
                    batch = []

            if batch:
                Employee.objects.bulk_create(batch, batch_size=batch_size)
                created += len(batch)

        elapsed = time.perf_counter() - start
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {created} employees in {elapsed:.2f}s '
                f'({first_names_path.name} x {last_names_path.name}).'
            )
        )
