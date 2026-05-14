import csv

from django.core.management.base import BaseCommand, CommandError

from journal.models import Journal
from plugins.health_dashboard.models import Category, JournalCategory
from utils.setting_handler import save_setting


class Command(BaseCommand):
    """Import journal data used by the dashboard"""
    help = "Import journal data used by the dashboard"

    def add_arguments(self, parser):
        parser.add_argument(
            "import_file", help="path to a csv file containing journal info", type=str
        )

    def handle(self, *args, **options):
        import_file = options.get("import_file")
        categories = [
            "Faculty Journal",
            "Graduate Student Journal",
            "Undergraduate",
            "Law Review",
            "Practitioner Journal",
            "Proceedings",
            "Non-Traditional Publication",
            "OJC Journal",
        ]

        with open(import_file, mode="r") as f:
            reader = csv.DictReader(f)

            for row in reader:
                print(row)
                if Journal.objects.filter(code=row["id"]):
                    j = Journal.objects.get(code=row["id"])
                    if row["Exclude from Reports and Dashboards"] != "TRUE":
                        save_setting(
                            "plugin:health_dashboard",
                            "dashboard_include",
                            j,
                            "on"
                        )
                    for c in categories:
                        if row[c] == "TRUE" or row[c] == "Yes":
                            category, _ = Category.objects.get_or_create(label=c)
                            JournalCategory.objects.get_or_create(
                                journal=j,
                                category=category
                            )
                    if "Campus Affiliation" in row:
                        category, _ = Category.objects.get_or_create(
                            label=row["Campus Affiliation"]
                        )
                        JournalCategory.objects.get_or_create(
                            journal=j,
                            category=category
                        )

