from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import include, path

from core.strategy_context import require_active_strategy
from .views import (
    handlungsfelder_table,
    massnahme_edit_page,
    level_crud,
    massnahmen_page,
    measure_type_crud,
    responsibility_crud,
    strategy_card_list,
    strategy_crud,
    ziele_page,
)


app_name = "strategies"

urlpatterns = [
    path("", login_required(lambda request: redirect("home")), name="list"),
    path("massnahmen/<pk>/edit/", login_required(require_active_strategy(massnahme_edit_page)), name="massnahme_edit"),
    path("levels/", include(level_crud)),
    path("handlungsfelder/", login_required(require_active_strategy(handlungsfelder_table.as_view())), name="handlungsfelder"),
    path("ziele/", login_required(require_active_strategy(ziele_page)), name="ziele"),
    path("massnahmen/", login_required(require_active_strategy(massnahmen_page)), name="massnahmen"),
    path("measure-types/", include(measure_type_crud)),
    path("responsibilities/", include(responsibility_crud)),
    *strategy_crud,
]
