from core.strategy_context import get_active_strategy
from core.versioning import get_app_version


def active_strategy(request):
    return {
        "active_strategy": get_active_strategy(request),
        "app_version": get_app_version(),
    }
