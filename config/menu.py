from iommi.main_menu import M, MainMenu

from core.strategy_context import get_active_strategy


def has_active_strategy(request):
    return get_active_strategy(request) is not None


main_menu = MainMenu(
    items=dict(
        home=M(
            view=lambda request: None,
            url=lambda user, **_: "/" if user.is_authenticated else None,
            display_name="Home",
            render=lambda user, **_: user.is_authenticated,
        ),
        dashboard=M(
            view=lambda request: None,
            url="/dashboard/",
            display_name="Dashboard",
            render=lambda user, **_: user.is_authenticated,
        ),
        handlungsfelder=M(
            view=lambda request: None,
            url=lambda request, **_: "/strategies/handlungsfelder/" if has_active_strategy(request) else "#",
            display_name="Handlungsfelder",
            render=lambda user, **_: user.is_authenticated,
            attrs__class__is_disabled=lambda request, user, **_: user.is_authenticated and not has_active_strategy(request),
        ),
        ziele=M(
            view=lambda request: None,
            url=lambda request, **_: "/strategies/ziele/" if has_active_strategy(request) else "#",
            display_name="Ziele",
            render=lambda user, **_: user.is_authenticated,
            attrs__class__is_disabled=lambda request, user, **_: user.is_authenticated and not has_active_strategy(request),
        ),
        massnahmen=M(
            view=lambda request: None,
            url=lambda request, **_: "/strategies/massnahmen/" if has_active_strategy(request) else "#",
            display_name="Massnahmen",
            render=lambda user, **_: user.is_authenticated,
            attrs__class__is_disabled=lambda request, user, **_: user.is_authenticated and not has_active_strategy(request),
        ),
        controlling_perioden=M(
            view=lambda request: None,
            url="/controlling/periods/",
            display_name="Controlling-Perioden",
            render=lambda user, **_: user.is_authenticated,
        ),
        controlling_records=M(
            view=lambda request: None,
            url=lambda request, **_: "/controlling/records/" if has_active_strategy(request) else "#",
            display_name="Controlling-Records",
            render=lambda user, **_: user.is_authenticated,
            attrs__class__is_disabled=lambda request, user, **_: user.is_authenticated and not has_active_strategy(request),
        ),
        personen=M(
            view=lambda request: None,
            url="/people/",
            display_name="Personen",
            render=lambda user, **_: user.is_authenticated,
        ),
        admin=M(
            view=lambda request: None,
            url="/admin/",
            display_name="Admin",
            render=lambda user, **_: user.is_authenticated and user.is_staff,
        ),
        login=M(
            view=lambda request: None,
            url="/accounts/login/",
            display_name="Login",
            render=lambda user, **_: not user.is_authenticated,
        ),
    )
)
