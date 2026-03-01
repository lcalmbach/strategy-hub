from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Runs migrations if requested and reloads the deterministic demo dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--migrate",
            action="store_true",
            help="Run migrations before loading demo data.",
        )
        parser.add_argument(
            "--no-replace",
            action="store_true",
            help="Keep existing demo rows and do not pass --replace to load_fake_data.",
        )

    def handle(self, *args, **options):
        if options["migrate"]:
            self.stdout.write("Running migrations...")
            call_command("migrate")

        self.stdout.write("Loading demo dataset...")
        load_options = {}
        if not options["no_replace"]:
            load_options["replace"] = True
        call_command("load_fake_data", **load_options)

        self.stdout.write(self.style.SUCCESS("Demo data bootstrap completed."))
