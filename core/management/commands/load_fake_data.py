import csv
import random
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Code
from controlling.models import (
    ControllingPeriod,
    ControllingRecord,
    ControllingRecordResponsibility,
    ControllingRecordStatus,
)
from people.models import Function, Organization, Person
from strategies.models import (
    MeasureResponsibility,
    MeasureType,
    ResponsibilityRole,
    Strategy,
    StrategyLevel,
    StrategyLevelType,
)


BASE_DIR = Path(__file__).resolve().parents[3]
FAKE_DATA_DIR = BASE_DIR / "fake_data"


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def as_date(value: str):
    value = value.strip()
    return date.fromisoformat(value) if value else None


def as_decimal(value: str) -> Decimal:
    value = value.strip()
    return Decimal(value) if value else Decimal("0.00")


def as_int(value: str):
    value = value.strip()
    return int(value) if value else None


def read_csv(filename: str):
    file_path = FAKE_DATA_DIR / filename
    if not file_path.exists():
        raise CommandError(f"CSV file not found: {file_path}")
    with file_path.open(newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


class Command(BaseCommand):
    help = "Loads deterministic fake data from ./fake_data CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing fake-data domain rows before importing CSV content.",
        )
        parser.add_argument(
            "--person",
            action="store_true",
            help="Load only users and people from the fake dataset.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        person_only = options["person"]

        if options["replace"]:
            if person_only:
                self._replace_people_data()
            else:
                self._replace_existing_data()

        self.stdout.write("Loading fake users...")
        self._load_users()

        self.stdout.write("Loading fake functions...")
        self._load_functions()
        self.stdout.write("Loading fake people...")
        people = self._load_people()

        if person_only:
            self.stdout.write(self.style.SUCCESS("Fake people import completed."))
            return

        self.stdout.write("Loading fake measure types...")
        measure_types = self._load_measure_types()

        self.stdout.write("Loading fake strategies...")
        strategies = self._load_strategies()

        self.stdout.write("Loading fake strategy levels...")
        levels = self._load_strategy_levels(strategies, measure_types)

        self.stdout.write("Loading fake measure responsibilities...")
        self._load_measure_responsibilities(people, levels)
        self._ensure_each_measure_has_responsible_people(people, levels)

        self.stdout.write("Loading fake controlling periods...")
        periods = self._load_controlling_periods()

        self.stdout.write("Loading fake controlling records...")
        records = self._load_controlling_records(periods, levels)

        self.stdout.write("Loading fake controlling record responsibilities...")
        self._load_controlling_record_responsibilities(people, periods, levels, records)

        self.stdout.write(self.style.SUCCESS("Fake data import completed."))

    def _replace_existing_data(self):
        self.stdout.write("Deleting existing imported domain data...")
        ControllingRecordResponsibility.objects.all().delete()
        ControllingRecord.objects.all().delete()
        ControllingPeriod.objects.all().delete()
        MeasureResponsibility.objects.all().delete()
        StrategyLevel.objects.all().delete()
        MeasureType.objects.all().delete()
        Strategy.objects.all().delete()
        Person.objects.all().delete()
        Organization.objects.all().delete()
        Function.objects.all().delete()

        usernames = [row["username"] for row in read_csv("users.csv")]
        get_user_model().objects.filter(username__in=usernames).delete()

    def _replace_people_data(self):
        self.stdout.write("Deleting existing imported people data...")
        Person.objects.all().delete()
        Organization.objects.all().delete()
        Function.objects.all().delete()

        usernames = [row["username"] for row in read_csv("users.csv")]
        get_user_model().objects.filter(username__in=usernames).delete()

    def _load_functions(self):
        function_map = {}
        for row in read_csv("functions.csv"):
            function, _ = Function.objects.update_or_create(
                code=row["code"],
                defaults={
                    "label": row["label"],
                    "sort_order": as_int(row.get("sort_order", "")) or 0,
                    "is_active": as_bool(row["is_active"]),
                },
            )
            function_map[function.code] = function
        return function_map

    def _load_users(self):
        User = get_user_model()
        user_map = {}
        for row in read_csv("users.csv"):
            user, _ = User.objects.update_or_create(
                username=row["username"],
                defaults={
                    "email": row["email"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "is_staff": as_bool(row["is_staff"]),
                    "is_superuser": as_bool(row["is_superuser"]),
                    "is_active": as_bool(row["is_active"]),
                },
            )
            user.set_password(row["password"])
            user.save(update_fields=["password"])
            user_map[user.username] = user
        return user_map

    def _load_people(self):
        people_map = {}
        users = get_user_model().objects.in_bulk(field_name="username")
        functions = Function.objects.in_bulk(field_name="code")
        organizations = {}
        for row in read_csv("people.csv"):
            user = users[row["username"]]
            org_name = row.get("organizational_unit", "").strip()
            organization = None
            if org_name:
                organization = organizations.get(org_name)
                if organization is None:
                    organization, _ = Organization.objects.get_or_create(
                        bereich=org_name,
                        abteilung="",
                        defaults={"is_active": True},
                    )
                    organizations[org_name] = organization
            person, _ = Person.objects.update_or_create(
                short_code=row["short_code"],
                defaults={
                    "user": user,
                    "function": functions[row["function_code"]],
                    "organization": organization,
                    "is_active_profile": as_bool(row["is_active_profile"]),
                },
            )
            people_map[person.short_code] = person
        return people_map

    def _load_measure_types(self):
        measure_type_map = {}
        for row in read_csv("measure_types.csv"):
            measure_type, _ = MeasureType.objects.update_or_create(
                code=row["code"],
                defaults={
                    "label": row["label"],
                    "is_active": as_bool(row["is_active"]),
                },
            )
            measure_type_map[measure_type.code] = measure_type
        return measure_type_map

    def _load_strategies(self):
        strategy_map = {}
        for row in read_csv("strategies.csv"):
            strategy, _ = Strategy.objects.update_or_create(
                short_code=row["short_code"],
                defaults={
                    "sort_order": as_int(row.get("sort_order", "")) or 0,
                    "short_code": row["short_code"],
                    "short_description": row["short_description"],
                    "title": row["title"],
                    "document_url": row["document_url"],
                    "valid_from": as_date(row["valid_from"]),
                    "valid_until": as_date(row["valid_until"]),
                    "status": row["status"],
                    "vision": row["vision"],
                    "mission": row["mission"],
                },
            )
            strategy.full_clean()
            strategy.save()
            strategy_map[strategy.title] = strategy
        return strategy_map

    def _load_strategy_levels(self, strategies, measure_types):
        level_rows = read_csv("strategy_levels.csv")
        levels = {}

        for row in level_rows:
            if row["parent_short_code"]:
                continue
            strategy = strategies[row["strategy_title"]]
            level, _ = StrategyLevel.objects.update_or_create(
                strategy=strategy,
                short_code=row["short_code"],
                defaults={
                    "level": row["level"],
                    "title": row["title"],
                    "description": row["description"],
                    "parent": None,
                    "sort_order": as_int(row["sort_order"]) or 0,
                    "measure_type": None,
                    "start_date": as_date(row.get("start_date", "")),
                    "end_date": as_date(row.get("end_date", "")),
                    "status": row.get("status", "") or None,
                },
            )
            level.full_clean()
            level.save()
            levels[(strategy.title, level.short_code)] = level

        remaining_rows = [row for row in level_rows if row["parent_short_code"]]
        while remaining_rows:
            loaded_any = False
            next_remaining = []
            for row in remaining_rows:
                strategy = strategies[row["strategy_title"]]
                parent_key = (strategy.title, row["parent_short_code"])
                parent = levels.get(parent_key)
                if parent is None:
                    next_remaining.append(row)
                    continue
                measure_type = measure_types.get(row["measure_type_code"]) if row["measure_type_code"] else None
                level, _ = StrategyLevel.objects.update_or_create(
                    strategy=strategy,
                    short_code=row["short_code"],
                    defaults={
                        "level": row["level"],
                        "title": row["title"],
                        "description": row["description"],
                        "parent": parent,
                        "sort_order": as_int(row["sort_order"]) or 0,
                        "measure_type": measure_type,
                        "start_date": as_date(row.get("start_date", "")),
                        "end_date": as_date(row.get("end_date", "")),
                        "status": row.get("status", "") or None,
                    },
                )
                level.full_clean()
                level.save()
                levels[(strategy.title, level.short_code)] = level
                loaded_any = True
            if not loaded_any and next_remaining:
                unresolved = ", ".join(row["short_code"] for row in next_remaining)
                raise CommandError(f"Could not resolve parent strategy levels for: {unresolved}")
            remaining_rows = next_remaining

        return levels

    def _load_measure_responsibilities(self, people, levels):
        for row in read_csv("measure_responsibilities.csv"):
            measure = levels[(row["strategy_title"], row["measure_short_code"])]
            person = people[row["person_short_code"]]
            responsibility, _ = MeasureResponsibility.objects.update_or_create(
                measure=measure,
                person=person,
                role=row["role"],
                defaults={
                    "valid_from": as_date(row["valid_from"]),
                    "valid_until": as_date(row["valid_until"]),
                },
            )
            responsibility.full_clean()
            responsibility.save()

    def _ensure_each_measure_has_responsible_people(self, people, levels):
        active_people = sorted(
            (person for person in people.values() if person.is_active_profile),
            key=lambda person: (person.user.last_name, person.user.first_name, person.short_code),
        )
        if not active_people:
            raise CommandError("At least one active person is required to assign Massnahme responsibilities.")

        generator = random.Random(0)
        measures = sorted(
            (
                level
                for level in levels.values()
                if level.level == StrategyLevelType.MASSNAHME
            ),
            key=lambda level: (level.strategy.title, level.short_code),
        )

        for measure in measures:
            existing_responsibilities = list(
                MeasureResponsibility.objects.filter(
                    measure=measure,
                    role=ResponsibilityRole.RESPONSIBLE,
                ).select_related("person")
            )
            target_count = generator.randint(1, min(2, len(active_people)))
            if len(existing_responsibilities) >= target_count:
                continue

            existing_person_ids = {responsibility.person_id for responsibility in existing_responsibilities}
            available_people = [person for person in active_people if person.pk not in existing_person_ids]
            additional_count = min(target_count - len(existing_responsibilities), len(available_people))
            for person in generator.sample(available_people, additional_count):
                responsibility = MeasureResponsibility(
                    measure=measure,
                    person=person,
                    role=ResponsibilityRole.RESPONSIBLE,
                )
                responsibility.full_clean()
                responsibility.save()

    def _load_controlling_periods(self):
        periods = {}
        for row in read_csv("controlling_periods.csv"):
            strategy = Strategy.objects.get(title=row["strategy_title"])
            period, _ = ControllingPeriod.objects.update_or_create(
                strategy=strategy,
                start_date=as_date(row["start_date"]),
                end_date=as_date(row["end_date"]),
                defaults={
                    "name": row["name"],
                    "planning_deadline": as_date(row["planning_deadline"]),
                    "controlling_deadline": as_date(row["controlling_deadline"]),
                    "status": row["status"],
                },
            )
            period.full_clean()
            period.save()
            periods[(strategy.title, period.name)] = period
        return periods

    def _load_controlling_records(self, periods, levels):
        status_mapping = {
            "open": ControllingRecordStatus.OPEN,
            "planning_in_progress": ControllingRecordStatus.PLANNING_IN_PROGRESS,
            "planning_completed": ControllingRecordStatus.PLANNING_COMPLETED,
            "ready_for_actuals": ControllingRecordStatus.CONTROLLING_IN_PROGRESS,
            "controlling_in_progress": ControllingRecordStatus.CONTROLLING_IN_PROGRESS,
            "completed": ControllingRecordStatus.CONTROLLING_COMPLETED,
            "controlling_completed": ControllingRecordStatus.CONTROLLING_COMPLETED,
        }
        records = {}
        for row in read_csv("controlling_records.csv"):
            period = periods[(row["strategy_title"], row["period_name"])]
            measure = levels[(row["strategy_title"], row["measure_short_code"])]
            mapped_status = status_mapping.get(row["status"], row["status"])
            status_code = Code.objects.get(category_id=1, code=mapped_status)
            record, _ = ControllingRecord.objects.update_or_create(
                period=period,
                measure=measure,
                defaults={
                    "status": status_code,
                    "plan_result_description": row["plan_result_description"],
                    "plan_effort_person_days": as_decimal(row["plan_effort_person_days"]),
                    "plan_effort_description": row["plan_effort_description"],
                    "plan_cost_chf": as_decimal(row["plan_cost_chf"]),
                    "plan_cost_description": row["plan_cost_description"],
                    "actual_fulfillment_percent": as_decimal(row["actual_fulfillment_percent"]),
                    "actual_result_description": row["actual_result_description"],
                    "actual_effort_person_days": as_decimal(row["actual_effort_person_days"]),
                    "actual_effort_description": row["actual_effort_description"],
                    "actual_cost_chf": as_decimal(row["actual_cost_chf"]),
                    "actual_cost_description": row["actual_cost_description"],
                },
            )
            record.full_clean()
            record.save()
            records[(period.name, measure.strategy.title, measure.short_code)] = record
        return records

    def _load_controlling_record_responsibilities(self, people, periods, levels, records):
        for row in read_csv("controlling_record_responsibilities.csv"):
            period = periods[(row["strategy_title"], row["period_name"])]
            measure = levels[(row["strategy_title"], row["measure_short_code"])]
            record = records[(period.name, measure.strategy.title, measure.short_code)]
            person = people[row["person_short_code"]]
            responsibility, _ = ControllingRecordResponsibility.objects.update_or_create(
                controlling_record=record,
                person=person,
                role=row["role"],
            )
            responsibility.full_clean()
            responsibility.save()
