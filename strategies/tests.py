from django.contrib.auth import get_user_model
from django.test import TestCase

from people.models import Function, Person
from strategies.models import MeasureResponsibility, ResponsibilityRole, Strategy, StrategyLevel, StrategyLevelType


class MassnahmeEditResponsibilitiesTest(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.editor = user_model.objects.create_user(
            username="editor",
            email="editor@example.com",
            password="password",
        )
        self.person_one_user = user_model.objects.create_user(
            username="person.one",
            email="person.one@example.com",
            password="password",
            first_name="Person",
            last_name="One",
        )
        self.person_two_user = user_model.objects.create_user(
            username="person.two",
            email="person.two@example.com",
            password="password",
            first_name="Person",
            last_name="Two",
        )

        self.function = Function.objects.create(
            code="LEAD",
            label="Lead",
            sort_order=10,
            is_active=True,
        )
        self.support_function = Function.objects.create(
            code="SUP",
            label="Support",
            sort_order=20,
            is_active=True,
        )

        self.person_one = Person.objects.create(
            user=self.person_one_user,
            short_code="P1",
            function=self.function,
            is_active_profile=True,
        )
        self.person_two = Person.objects.create(
            user=self.person_two_user,
            short_code="P2",
            function=self.support_function,
            is_active_profile=True,
        )

        self.strategy = Strategy.objects.create(
            short_code="TS",
            title="Test Strategy",
            short_description="Short description",
            valid_from="2026-01-01",
            status="active",
            vision="Vision",
            mission="Mission",
        )
        self.handlungsfeld = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.HANDLUNGSFELD,
            title="Handlungsfeld",
            short_code="HF-1",
            sort_order=10,
        )
        self.ziel = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.ZIEL,
            title="Ziel",
            short_code="Z-1",
            parent=self.handlungsfeld,
            sort_order=20,
        )
        self.massnahme = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Massnahme",
            short_code="M-1",
            parent=self.ziel,
            sort_order=30,
            status="planned",
        )

        self.client.force_login(self.editor)
        session = self.client.session
        session["active_strategy_id"] = self.strategy.pk
        session.save()

    def test_massnahme_edit_page_allows_multiple_responsibilities(self):
        response = self.client.get(f"/strategies/massnahmen/{self.massnahme.pk}/edit/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verantwortlichkeiten")
        self.assertContains(response, 'name="responsibilities-0-person"', html=False)
        self.assertContains(response, 'name="responsibilities-0-role"', html=False)
        self.assertContains(response, 'name="responsibilities-0-description"', html=False)

        response = self.client.post(
            f"/strategies/massnahmen/{self.massnahme.pk}/edit/",
            data={
                "title": self.massnahme.title,
                "short_code": self.massnahme.short_code,
                "description": self.massnahme.description,
                "parent": str(self.ziel.pk),
                "measure_type": "",
                "start_date": "",
                "end_date": "",
                "status": "planned",
                "sort_order": str(self.massnahme.sort_order),
                "responsibilities-TOTAL_FORMS": "5",
                "responsibilities-INITIAL_FORMS": "0",
                "responsibilities-MIN_NUM_FORMS": "0",
                "responsibilities-MAX_NUM_FORMS": "1000",
                "responsibilities-0-person": str(self.person_one.pk),
                "responsibilities-0-role": ResponsibilityRole.RESPONSIBLE,
                "responsibilities-0-description": "Lead owner for delivery",
                "responsibilities-1-person": str(self.person_two.pk),
                "responsibilities-1-role": ResponsibilityRole.SUPPORTING,
                "responsibilities-1-description": "Supports execution and coordination",
                "responsibilities-2-person": "",
                "responsibilities-2-role": "",
                "responsibilities-2-description": "",
                "responsibilities-3-person": "",
                "responsibilities-3-role": "",
                "responsibilities-3-description": "",
                "responsibilities-4-person": "",
                "responsibilities-4-role": "",
                "responsibilities-4-description": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        responsibilities = list(
            MeasureResponsibility.objects.filter(measure=self.massnahme).order_by("person__short_code", "role")
        )
        self.assertEqual(len(responsibilities), 2)
        self.assertEqual(responsibilities[0].person, self.person_one)
        self.assertEqual(responsibilities[0].role, ResponsibilityRole.RESPONSIBLE)
        self.assertEqual(responsibilities[0].description, "Lead owner for delivery")
        self.assertEqual(responsibilities[1].person, self.person_two)
        self.assertEqual(responsibilities[1].role, ResponsibilityRole.SUPPORTING)
        self.assertEqual(responsibilities[1].description, "Supports execution and coordination")

    def test_massnahmen_list_shows_comma_separated_responsible_people(self):
        MeasureResponsibility.objects.create(
            measure=self.massnahme,
            person=self.person_one,
            role=ResponsibilityRole.RESPONSIBLE,
        )
        MeasureResponsibility.objects.create(
            measure=self.massnahme,
            person=self.person_two,
            role=ResponsibilityRole.SUPPORTING,
        )

        response = self.client.get("/strategies/massnahmen/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "P1, P2")
