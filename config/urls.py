from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from iommi.views import auth_views

from dashboard.views import dashboard_home, help_page, logout_view, profile_page, select_strategy
from strategies.views import strategy_card_list


urlpatterns = [
    path("", strategy_card_list, name="home"),
    path("dashboard/", dashboard_home, name="dashboard"),
    path("hilfe/", help_page, name="help"),
    path("accounts/logout/", logout_view, name="logout"),
    path("accounts/profile/", profile_page, name="profile"),
    path("select-strategy/<int:strategy_id>/", select_strategy, name="select-strategy"),
    path("admin/", admin.site.urls),
    path("accounts/", auth_views()),
    path("strategies/", include("strategies.urls")),
    path("controlling/", include("controlling.urls")),
    path("people/", include("people.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
