from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import Code
from controlling.models import ControllingPeriod, ControllingRecord, ControllingRecordStatus
from strategies.models import Strategy, StrategyLevel, StrategyLevelType


class GenerateMissingRecordsForPeriodTest(TestCase):
    def setUp(self):
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
