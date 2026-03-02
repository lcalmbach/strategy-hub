import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from controlling.models import (
    ControllingPeriod,
    ControllingRecord,
    ControllingRecordResponsibility,
)
from people.models import Person
from strategies.models import MeasureResponsibility, MeasureType, Strategy, StrategyLevel


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

    @transaction.atomic
    def handle(self, *args, **options):
        if options["replace"]:
            self._replace_existing_data()

        self.stdout.write("Loading fake users...")
        users = self._load_users()

        self.stdout.write("Loading fake people...")
        people = self._load_people()

        self.stdout.write("Loading fake measure types...")
        measure_types = self._load_measure_types()

        self.stdout.write("Loading fake strategies...")
        strategies = self._load_strategies()

        self.stdout.write("Loading fake strategy levels...")
        levels = self._load_strategy_levels(strategies, measure_types)

        self.stdout.write("Loading fake measure responsibilities...")
        self._load_measure_responsibilities(people, levels)

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

        usernames = [row["username"] for row in read_csv("users.csv")]
        get_user_model().objects.filter(username__in=usernames).delete()

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
        for row in read_csv("people.csv"):
            user = users[row["username"]]
            person, _ = Person.objects.update_or_create(
                short_code=row["short_code"],
                defaults={
                    "user": user,
                    "function_title": row["function_title"],
                    "organizational_unit": row["organizational_unit"],
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
                title=row["title"],
                defaults={
                    "short_description": row["short_description"],
                    "document_url": row["document_url"],
                    "valid_from": as_date(row["valid_from"]),
                    "valid_until": as_date(row["valid_until"]),
                    "status": row["status"],
                    "vision": row["vision"],
                    "mission": row["mission"],
                    "is_active": as_bool(row["is_active"]),
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
                    "actuals_deadline": as_date(row["actuals_deadline"]),
                    "status": row["status"],
                    "is_locked": as_bool(row["is_locked"]),
                },
            )
            period.full_clean()
            period.save()
            periods[(strategy.title, period.name)] = period
        return periods

    def _load_controlling_records(self, periods, levels):
        records = {}
        for row in read_csv("controlling_records.csv"):
            period = periods[(row["strategy_title"], row["period_name"])]
            measure = levels[(row["strategy_title"], row["measure_short_code"])]
            record, _ = ControllingRecord.objects.update_or_create(
                period=period,
                measure=measure,
                defaults={
                    "status": row["status"],
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
