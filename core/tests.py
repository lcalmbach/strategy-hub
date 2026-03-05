from django.contrib.auth import get_user_model
from django.test import TestCase

from core.management.commands.load_fake_data import Command
from core.models import Code, CodeCategoryKeys, InitiativeStatusCode
from people.models import Function, Person
from strategies.models import MeasureResponsibility, ResponsibilityRole, Strategy, StrategyLevel, StrategyLevelType


class LoadFakeDataCommandTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
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
            is_active=True,
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
        self.massnahme_without_responsible = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Massnahme One",
            short_code="M-1",
            parent=self.ziel,
            sort_order=30,
            status="planned",
        )
        self.massnahme_with_responsible = StrategyLevel.objects.create(
            strategy=self.strategy,
            level=StrategyLevelType.MASSNAHME,
            title="Massnahme Two",
            short_code="M-2",
            parent=self.ziel,
            sort_order=40,
            status="planned",
        )

    def test_assigns_one_or_two_responsible_people_to_each_massnahme(self):
        MeasureResponsibility.objects.create(
            measure=self.massnahme_with_responsible,
            person=self.person_one,
            role=ResponsibilityRole.RESPONSIBLE,
        )

        command = Command()
        people = {
            self.person_one.short_code: self.person_one,
            self.person_two.short_code: self.person_two,
        }
        levels = {
            (self.strategy.title, self.massnahme_without_responsible.short_code): self.massnahme_without_responsible,
            (self.strategy.title, self.massnahme_with_responsible.short_code): self.massnahme_with_responsible,
        }

        command._ensure_each_measure_has_responsible_people(people, levels)

        generated_responsibilities = MeasureResponsibility.objects.filter(
            measure=self.massnahme_without_responsible,
            role=ResponsibilityRole.RESPONSIBLE,
        )
        self.assertGreaterEqual(generated_responsibilities.count(), 1)
        self.assertLessEqual(generated_responsibilities.count(), 2)
        self.assertTrue(all(r.person in {self.person_one, self.person_two} for r in generated_responsibilities))

        existing_responsibilities = MeasureResponsibility.objects.filter(
            measure=self.massnahme_with_responsible,
            role=ResponsibilityRole.RESPONSIBLE,
        )
        self.assertGreaterEqual(existing_responsibilities.count(), 1)
        self.assertLessEqual(existing_responsibilities.count(), 2)
        self.assertEqual(existing_responsibilities.filter(person=self.person_one).count(), 1)


class CategoryCodeManagerTest(TestCase):
    def test_proxy_manager_uses_fixed_category_and_filters_by_it(self):
        created = InitiativeStatusCode.objects.create(
            code="planned",
            name="Geplant",
            short_name="Planned",
            sort_order=10,
        )

        self.assertEqual(created.category.key, CodeCategoryKeys.INITIATIVE_STATUS)
        self.assertEqual(InitiativeStatusCode.objects.count(), 1)
        self.assertEqual(
            Code.objects.filter(category__key=CodeCategoryKeys.INITIATIVE_STATUS).count(),
            1,
        )
