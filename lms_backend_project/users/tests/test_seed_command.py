import shutil
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings


class SeedCommandTests(TestCase):
    def setUp(self):
        # Create a temporary media root for test files
        self.tmp_media = tempfile.mkdtemp(prefix="test_media_")

    def tearDown(self):
        # Remove temp dir
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def test_seed_creates_records_and_files(self):
        with override_settings(MEDIA_ROOT=self.tmp_media):
            # Run seed command
            call_command("seed_mock_data")

            # Basic assertions: the command should create simulation and loan application records
            from loans.models import LoanApplication
            from simulations.models import SimulationHeader

            self.assertTrue(SimulationHeader.objects.exists())
            self.assertTrue(LoanApplication.objects.exists())

            # Documents should have files saved under MEDIA_ROOT
            from documents.models import Document

            doc = Document.objects.first()
            self.assertIsNotNone(doc)
            self.assertTrue(doc.file and doc.file.name)

    def test_seed_idempotent_on_second_run(self):
        with override_settings(MEDIA_ROOT=self.tmp_media):
            call_command("seed_mock_data")
            from documents.models import Document
            from loans.models import LoanApplication
            from simulations.models import SimulationHeader

            sim_count = SimulationHeader.objects.count()
            app_count = LoanApplication.objects.count()
            doc_count = Document.objects.count()

            # Run again
            call_command("seed_mock_data")

            # Counts should not have multiplied
            self.assertEqual(sim_count, SimulationHeader.objects.count())
            self.assertEqual(app_count, LoanApplication.objects.count())
            # Documents may be created per application. Because the seeder skips creating
            # applications when the user already has them, the document count should
            # remain unchanged after a second run of the seed command.
            self.assertEqual(doc_count, Document.objects.count())
