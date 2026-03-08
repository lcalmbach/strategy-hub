from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from core.models import Code, CodeCategory
from controlling.models import (
    ControllingPeriod,
    ControllingRecord,
    ControllingRecordResponsibility,
    ControllingRecordStatus,
)
from people.models import Function, Person
from strategies.models import (
    MeasureResponsibility,
    ResponsibilityRole,
    Strategy,
    StrategyLevel,
    StrategyLevelType,
)


def ensure_controlling_status_codes():
    category, _ = CodeCategory.objects.get_or_create(
        id=1,
        defaults={
            "key": "controlling_record_status",
            "name": "Controlling-Record-Status",
            "sort_order": 1,
        },
    )
    for index, status in enumerate(ControllingRecordStatus, start=1):
        Code.objects.get_or_create(
            category=category,
            code=status.value,
            defaults={
                "name": status.label,
                "short_name": status.label,
                "sort_order": index,
            },
        )


class GenerateMissingRecordsForPeriodTest(TestCase):
    def setUp(self):
        ensure_controlling_status_codes()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="controller",
            email="controller@example.com",
            password="password",
        )

        self.strategy = Strategy.objects.create(
            short_code="STR-A",
            title="Strategy A",
            short_description="Strategy A description",
            valid_from="2026-01-01",
            status="active",
            vision="Vision A",
            mission="Mission A",
        )
        self.other_strategy = Strategy.objects.create(
            short_code="STR-B",
            title="Strategy B",
            short_description="Strategy B description",
            valid_from="2026-01-01",
            status="active",
            vision="Vision B",
            mission="Mission B",
        )

        handlungsfeld = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.HANDLUNGSFELD,
            title="HF A",
            short_code="HF-A",
            sort_order=10,
        )
        ziel = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.ZIEL,
            title="Ziel A",
            short_code="Z-A",
            parent=handlungsfeld,
            sort_order=20,
        )
        self.measure_1 = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Massnahme A1",
            short_code="M-A1",
            parent=ziel,
            sort_order=30,
            status="planned",
        )
        self.measure_2 = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Massnahme A2",
            short_code="M-A2",
            parent=ziel,
            sort_order=40,
            status="planned",
        )
        self.measure_3 = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Massnahme A3",
            short_code="M-A3",
            parent=ziel,
            sort_order=50,
            status="planned",
        )

        other_handlungsfeld = StrategyLevel.objects.create(
            strategy=self.other_strategy,
            level=StrategyLevelType.HANDLUNGSFELD,
            title="HF B",
            short_code="HF-B",
            sort_order=10,
        )
        other_ziel = StrategyLevel.objects.create(
            strategy=self.other_strategy,
            level=StrategyLevelType.ZIEL,
            title="Ziel B",
            short_code="Z-B",
            parent=other_handlungsfeld,
            sort_order=20,
        )
        self.other_measure = StrategyLevel.objects.create(
            strategy=self.other_strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Massnahme B1",
            short_code="M-B1",
            parent=other_ziel,
            sort_order=30,
            status="planned",
        )

        self.period = ControllingPeriod.objects.create(
            strategy=self.strategy,
            name="Q1 2026",
            start_date="2026-01-01",
            end_date="2026-03-31",
            status="open_for_planning",
        )
        open_status = Code.objects.get(category_id=1, code=ControllingRecordStatus.OPEN)
        ControllingRecord.objects.create(
            period=self.period,
            measure=self.measure_1,
            status=open_status,
        )

        self.client.force_login(self.user)
        session = self.client.session
        session["active_strategy_id"] = self.strategy.pk
        session.save()

    def test_generate_missing_records_for_period_creates_only_missing_for_strategy(self):
        response = self.client.get(f"/controlling/periods/{self.period.pk}/generate-missing-records/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/controlling/periods/{self.period.pk}/")

        records = ControllingRecord.objects.filter(period=self.period).order_by("measure__short_code")
        self.assertEqual(records.count(), 3)
        self.assertTrue(records.filter(measure=self.measure_1).exists())
        self.assertTrue(records.filter(measure=self.measure_2).exists())
        self.assertTrue(records.filter(measure=self.measure_3).exists())
        self.assertFalse(records.filter(measure=self.other_measure).exists())


class ControllingRecordListOrderingTest(TestCase):
    def setUp(self):
        ensure_controlling_status_codes()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="ordering-user",
            email="ordering-user@example.com",
            password="password",
        )
        self.client.force_login(self.user)

        self.strategy = Strategy.objects.create(
            short_code="STR-ORDER",
            title="Ordering Strategy",
            short_description="Ordering description",
            valid_from="2026-01-01",
            status="active",
            vision="Vision",
            mission="Mission",
        )

        handlungsfeld = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.HANDLUNGSFELD,
            title="HF",
            short_code="HF-1",
            sort_order=10,
        )
        ziel = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.ZIEL,
            title="Ziel",
            short_code="Z-1",
            parent=handlungsfeld,
            sort_order=20,
        )

        measure_late_1 = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Measure Late 20",
            short_code="M-L20",
            parent=ziel,
            sort_order=20,
            status="planned",
        )
        measure_late_2 = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Measure Late 10",
            short_code="M-L10",
            parent=ziel,
            sort_order=10,
            status="planned",
        )
        measure_early_1 = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Measure Early 30",
            short_code="M-E30",
            parent=ziel,
            sort_order=30,
            status="planned",
        )
        measure_early_2 = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Measure Early 15",
            short_code="M-E15",
            parent=ziel,
            sort_order=15,
            status="planned",
        )

        period_early = ControllingPeriod.objects.create(
            strategy=self.strategy,
            name="Q1 2026",
            start_date="2026-01-01",
            end_date="2026-03-31",
            status="open_for_planning",
        )
        period_late = ControllingPeriod.objects.create(
            strategy=self.strategy,
            name="Q2 2026",
            start_date="2026-04-01",
            end_date="2026-06-30",
            status="open_for_planning",
        )
        open_status = Code.objects.get(category_id=1, code=ControllingRecordStatus.OPEN)

        ControllingRecord.objects.create(period=period_late, measure=measure_late_1, status=open_status)
        ControllingRecord.objects.create(period=period_late, measure=measure_late_2, status=open_status)
        ControllingRecord.objects.create(period=period_early, measure=measure_early_1, status=open_status)
        ControllingRecord.objects.create(period=period_early, measure=measure_early_2, status=open_status)

        session = self.client.session
        session["active_strategy_id"] = self.strategy.pk
        session.save()

    def test_records_are_sorted_by_period_desc_then_measure_sort_order(self):
        response = self.client.get("/controlling/records/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        late_10_pos = content.find("M-L10 Measure Late 10")
        late_20_pos = content.find("M-L20 Measure Late 20")
        early_15_pos = content.find("M-E15 Measure Early 15")
        early_30_pos = content.find("M-E30 Measure Early 30")

        self.assertGreaterEqual(late_10_pos, 0)
        self.assertGreaterEqual(late_20_pos, 0)
        self.assertGreaterEqual(early_15_pos, 0)
        self.assertGreaterEqual(early_30_pos, 0)
        self.assertLess(late_10_pos, late_20_pos)
        self.assertLess(late_20_pos, early_15_pos)
        self.assertLess(early_15_pos, early_30_pos)


class GenerateControllingRecordsBackfillTest(TestCase):
    def setUp(self):
        ensure_controlling_status_codes()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="backfill-user",
            email="backfill-user@example.com",
            password="password",
            first_name="Backfill",
            last_name="User",
        )
        self.function = Function.objects.create(
            code="FUNC",
            label="Function",
            sort_order=10,
            is_active=True,
        )
        self.person = Person.objects.create(
            user=self.user,
            short_code="BFU",
            function=self.function,
            is_active_profile=True,
        )
        self.strategy = Strategy.objects.create(
            short_code="STR-BF",
            title="Backfill Strategy",
            short_description="Backfill description",
            valid_from="2026-01-01",
            status="active",
            vision="Vision",
            mission="Mission",
        )
        handlungsfeld = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.HANDLUNGSFELD,
            title="HF",
            short_code="HF",
            sort_order=10,
        )
        ziel = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.ZIEL,
            title="Ziel",
            short_code="Z",
            parent=handlungsfeld,
            sort_order=20,
        )
        self.measure_missing = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Missing Data Measure",
            short_code="M-MISS",
            parent=ziel,
            sort_order=30,
            status="planned",
        )
        self.measure_existing = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Existing Data Measure",
            short_code="M-EXIST",
            parent=ziel,
            sort_order=40,
            status="planned",
        )
        self.period = ControllingPeriod.objects.create(
            strategy=self.strategy,
            name="Q1 2026",
            start_date="2026-01-01",
            end_date="2026-03-31",
            status="open_for_planning",
        )
        open_status = Code.objects.get(category_id=1, code=ControllingRecordStatus.OPEN)
        self.record_missing = ControllingRecord.objects.create(
            period=self.period,
            measure=self.measure_missing,
            status=open_status,
        )
        self.record_existing = ControllingRecord.objects.create(
            period=self.period,
            measure=self.measure_existing,
            status=open_status,
            plan_result_description="Bestehende Planung",
            plan_effort_person_days="12.00",
            plan_effort_description="Bereits gesetzt",
            plan_cost_chf="25000.00",
            plan_cost_description="Bereits gesetzt",
            actual_fulfillment_percent="66.00",
            actual_result_description="Bestehendes Ist",
            actual_effort_person_days="10.00",
            actual_effort_description="Bereits gesetzt",
            actual_cost_chf="22000.00",
            actual_cost_description="Bereits gesetzt",
        )
        MeasureResponsibility.objects.create(
            measure=self.measure_missing,
            person=self.person,
            role=ResponsibilityRole.RESPONSIBLE,
        )

    def test_command_backfills_missing_responsibilities_and_fake_values(self):
        call_command("generate_controlling_records")

        self.record_missing.refresh_from_db()
        responsibilities = ControllingRecordResponsibility.objects.filter(controlling_record=self.record_missing)
        self.assertEqual(responsibilities.count(), 1)
        self.assertEqual(responsibilities.first().person, self.person)
        self.assertGreater(self.record_missing.plan_effort_person_days, 0)
        self.assertGreater(self.record_missing.plan_cost_chf, 0)
        self.assertTrue(self.record_missing.plan_result_description)
        self.assertGreater(self.record_missing.actual_fulfillment_percent, 0)
        self.assertGreater(self.record_missing.actual_effort_person_days, 0)
        self.assertGreater(self.record_missing.actual_cost_chf, 0)
        self.assertTrue(self.record_missing.actual_result_description)

    def test_command_does_not_override_existing_planning_and_actual_values(self):
        call_command("generate_controlling_records")

        self.record_existing.refresh_from_db()
        self.assertEqual(self.record_existing.plan_result_description, "Bestehende Planung")
        self.assertEqual(str(self.record_existing.plan_effort_person_days), "12.00")
        self.assertEqual(str(self.record_existing.plan_cost_chf), "25000.00")
        self.assertEqual(self.record_existing.actual_result_description, "Bestehendes Ist")
        self.assertEqual(str(self.record_existing.actual_fulfillment_percent), "66.00")
        self.assertEqual(str(self.record_existing.actual_effort_person_days), "10.00")
        self.assertEqual(str(self.record_existing.actual_cost_chf), "22000.00")
