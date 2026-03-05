from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        abstract = True


class UserStampedModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Erstellt von",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Aktualisiert von",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    sort_order = models.PositiveIntegerField("Sortierung", default=0)

    class Meta:
        abstract = True


class CodeCategory(TimestampedModel, UserStampedModel, OrderedModel):
    key = models.SlugField("Schlüssel", max_length=100, unique=True)
    name = models.CharField("Name", max_length=255, unique=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Code-Kategorie"
        verbose_name_plural = "Code-Kategorien"

    def __str__(self) -> str:
        return self.name


class CodeCategoryKeys:
    INITIATIVE_STATUS = "initiative_status"
    INITIATIVE_ROLE = "initiative_role"


class CategoryCodeManager(models.Manager):
    category_key: str | None = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.category_key:
            return queryset.filter(category__key=self.category_key)
        return queryset

    def get_by_code(self, code: str):
        return self.get(code=code)

    def create(self, **kwargs):
        if self.category_key and "category" not in kwargs and "category_id" not in kwargs:
            kwargs["category"] = CodeCategory.objects.get(key=self.category_key)
        return super().create(**kwargs)


class Code(TimestampedModel, UserStampedModel, OrderedModel):
    category = models.ForeignKey(
        CodeCategory,
        verbose_name="Kategorie",
        on_delete=models.PROTECT,
        related_name="codes",
    )
    code = models.CharField("Code", max_length=100)
    name = models.CharField("Name", max_length=255)
    short_name = models.CharField("Kurzname", max_length=100, blank=True)

    objects = CategoryCodeManager()

    class Meta:
        ordering = ["category__sort_order", "category__name", "sort_order", "name"]
        verbose_name = "Code"
        verbose_name_plural = "Codes"
        constraints = [
            models.UniqueConstraint(fields=["category", "code"], name="uniq_code_by_category"),
            models.UniqueConstraint(fields=["category", "name"], name="uniq_code_name_by_category"),
        ]

    def __str__(self) -> str:
        return f"{self.category.name}: {self.name}"


class InitiativeStatusCodeManager(CategoryCodeManager):
    category_key = CodeCategoryKeys.INITIATIVE_STATUS


class InitiativeRoleCodeManager(CategoryCodeManager):
    category_key = CodeCategoryKeys.INITIATIVE_ROLE


class InitiativeStatusCode(Code):
    objects = InitiativeStatusCodeManager()

    class Meta:
        proxy = True
        verbose_name = "Initiative-Status"
        verbose_name_plural = "Initiative-Status"


class InitiativeRoleCode(Code):
    objects = InitiativeRoleCodeManager()

    class Meta:
        proxy = True
        verbose_name = "Initiative-Rolle"
        verbose_name_plural = "Initiative-Rollen"
