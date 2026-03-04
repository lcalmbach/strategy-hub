from functools import wraps

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from strategies.models import Strategy


ACTIVE_STRATEGY_SESSION_KEY = "active_strategy_id"


def get_active_strategy_id(request):
    return request.session.get(ACTIVE_STRATEGY_SESSION_KEY)


def get_active_strategy(request):
    strategy_id = get_active_strategy_id(request)
    if not strategy_id:
        return None
    return Strategy.objects.filter(pk=strategy_id).first()


def set_active_strategy(request, strategy):
    request.session[ACTIVE_STRATEGY_SESSION_KEY] = strategy.pk
    request.session.modified = True


def require_active_strategy(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if get_active_strategy(request) is None:
            messages.warning(request, "Bitte wähle zuerst auf der Startseite eine Strategie aus.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return wrapped


def select_active_strategy(request, strategy_id):
    strategy = get_object_or_404(Strategy, pk=strategy_id, is_active=True)
    set_active_strategy(request, strategy)
    messages.success(request, f"Aktive Strategie gesetzt: {strategy.title}")
    return strategy
