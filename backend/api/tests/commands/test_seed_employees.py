import math
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase, override_settings

from api.models import Employee
from api.utils.management.commands.seed_employees import DATA_DIR, load_names


def expected_seed_query_count(*, count: int, batch_size: int, clear: bool = False) -> int:
    """
    Expected DB queries for seed_employees on SQLite inside transaction.atomic().

    - 2 queries for BEGIN/COMMIT
    - 1 DELETE when --clear is set
    - ceil(count / batch_size) bulk_create INSERT batches when count > 0
    """
    insert_batches = math.ceil(count / batch_size) if count > 0 else 0
    delete_queries = 1 if clear else 0
    return 2 + delete_queries + insert_batches


class SeedEmployeesCommandTests(TestCase):
    """
    Tests for seed_employees management command.

    Covered cases:
    - Seeding with count creates the expected number of employees.
    - Seeded first names come from first_names.txt.
    - Clear flag replaces existing employees with seeded count.
    - Same seed produces reproducible first employee name.
    - Repeated runs without clear accumulate employee rows.
    - Query count matches bulk_create batching and optional clear delete.
    """

    def test_seed_employees__count_five__creates_five_rows(self):
        """Seeding with count creates the expected number of employees."""
        # GIVEN
        initial_count = Employee.objects.count()

        # WHEN
        call_command('seed_employees', count=5, seed=99)

        # THEN
        self.assertEqual(Employee.objects.count(), initial_count + 5)

    def test_seed_employees__seeded_names__from_first_names_file(self):
        """Seeded first names come from first_names.txt."""
        # GIVEN
        first_names = load_names(DATA_DIR / 'first_names.txt')
        call_command('seed_employees', count=3, seed=7, clear=True)

        # WHEN
        employee = Employee.objects.order_by('id').first()

        # THEN
        self.assertIn(employee.first_name, first_names)

    def test_seed_employees__clear_flag__replaces_existing_rows(self):
        """Clear flag replaces existing employees with seeded count."""
        # GIVEN
        call_command('seed_employees', count=4, seed=1)

        # WHEN
        call_command('seed_employees', count=3, seed=2, clear=True)

        # THEN
        self.assertEqual(Employee.objects.count(), 3)

    def test_seed_employees__same_seed__reproducible_first_name(self):
        """Same seed produces reproducible first employee name."""
        # GIVEN / WHEN
        call_command('seed_employees', count=2, seed=123, clear=True)
        first_run = Employee.objects.order_by('id').first().first_name

        call_command('seed_employees', count=2, seed=123, clear=True)
        second_run = Employee.objects.order_by('id').first().first_name

        # THEN
        self.assertEqual(first_run, second_run)

    def test_seed_employees__without_clear_twice__accumulates_rows(self):
        """Repeated runs without clear add employees instead of replacing them."""
        # GIVEN
        call_command('seed_employees', count=3, seed=10, clear=True)

        # WHEN
        call_command('seed_employees', count=2, seed=20)
        call_command('seed_employees', count=4, seed=30)

        # THEN
        self.assertEqual(Employee.objects.count(), 9)

    def test_seed_employees__query_count__single_batch_without_clear(self):
        """Seeding uses one bulk insert batch when count fits in batch_size."""
        # GIVEN
        count = 5
        batch_size = 1000
        expected_queries = expected_seed_query_count(
            count=count,
            batch_size=batch_size,
            clear=False,
        )

        # WHEN / THEN
        with self.assertNumQueries(expected_queries):
            call_command('seed_employees', count=count, seed=1, batch_size=batch_size)

    def test_seed_employees__query_count__clear_and_multiple_batches(self):
        """Seeding with clear and multiple batches issues delete plus batched inserts."""
        # GIVEN
        count = 2500
        batch_size = 1000
        expected_queries = expected_seed_query_count(
            count=count,
            batch_size=batch_size,
            clear=True,
        )

        # WHEN / THEN
        with self.assertNumQueries(expected_queries):
            call_command(
                'seed_employees',
                count=count,
                seed=1,
                batch_size=batch_size,
                clear=True,
            )


class SeedEmployeesCommandEdgeTests(TestCase):
    """
    Edge-case tests for seed_employees management command.

    These capture boundary behavior; failures indicate follow-up work in the
    command implementation.
    """

    def test_seed_employees__count_zero__creates_no_rows(self):
        """Seeding with count zero should not create employees."""
        # GIVEN
        call_command('seed_employees', count=2, seed=1, clear=True)

        # WHEN
        call_command('seed_employees', count=0, seed=1)

        # THEN
        self.assertEqual(Employee.objects.count(), 2)

    def test_seed_employees__count_zero__query_count_without_inserts(self):
        """Seeding with count zero should only run transaction wrapper queries."""
        # GIVEN
        expected_queries = expected_seed_query_count(count=0, batch_size=1000, clear=False)

        # WHEN / THEN
        with self.assertNumQueries(expected_queries):
            call_command('seed_employees', count=0, seed=1, clear=True)

    def test_seed_employees__negative_count__raises_or_creates_nothing(self):
        """Negative count should be rejected or create no employees."""
        # GIVEN
        call_command('seed_employees', count=1, seed=1, clear=True)

        # WHEN
        call_command('seed_employees', count=-5, seed=1)

        # THEN
        self.assertEqual(Employee.objects.count(), 1)

    def test_seed_employees__missing_name_files__creates_no_rows(self):
        """Missing name files should abort seeding without creating employees."""
        # GIVEN
        with tempfile.TemporaryDirectory() as tmp_dir:
            err = StringIO()
            with override_settings(BASE_DIR=tmp_dir):
                # WHEN
                call_command('seed_employees', count=5, seed=1, stderr=err)

            # THEN
            self.assertEqual(Employee.objects.count(), 0)
            self.assertIn('Name files required', err.getvalue())

    def test_seed_employees__empty_name_files__creates_no_rows(self):
        """Empty name files should abort seeding without creating employees."""
        # GIVEN
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir) / 'data'
            data_dir.mkdir()
            (data_dir / 'first_names.txt').write_text('\n\n', encoding='utf-8')
            (data_dir / 'last_names.txt').write_text('Doe\n', encoding='utf-8')
            err = StringIO()
            with override_settings(BASE_DIR=tmp_dir):
                # WHEN
                call_command('seed_employees', count=5, seed=1, stderr=err)

            # THEN
            self.assertEqual(Employee.objects.count(), 0)
            self.assertIn('must not be empty', err.getvalue())

    def test_seed_employees__batch_size_larger_than_count__single_insert_batch(self):
        """batch_size greater than count should still issue a single insert batch."""
        # GIVEN
        expected_queries = expected_seed_query_count(count=3, batch_size=10_000, clear=True)

        # WHEN / THEN
        with self.assertNumQueries(expected_queries):
            call_command('seed_employees', count=3, seed=1, batch_size=10_000, clear=True)

        self.assertEqual(Employee.objects.count(), 3)

    def test_seed_employees__duplicate_slug_collision__second_run_without_clear_fails(self):
        """
        Re-seeding with the same seed and indexes can duplicate unique emails.

        This documents that callers should use --clear or unique seeds when re-running.
        """
        # GIVEN
        call_command('seed_employees', count=2, seed=99, clear=True)

        # WHEN / THEN
        with self.assertRaises(IntegrityError):
            call_command('seed_employees', count=2, seed=99)
