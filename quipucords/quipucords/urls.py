"""quipucords URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))

"""

from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", RedirectView.as_view(url="/login", permanent=False), name="home"),
    # ui routing
    re_path(
        r"^(client/(sources|scans|credentials|)(/|)(index.html|))$",
        TemplateView.as_view(template_name="client/index.html"),
        name="client",
    ),
    # docs files
    re_path(
        r"^client/docs(/|)(index.html|use.html|)$",
        RedirectView.as_view(url="/client/docs/use.html", permanent=False),
        name="docs",
    ),
    re_path(
        r"^client/docs(/|)(install.html|)$",
        RedirectView.as_view(url="/client/docs/install.html", permanent=False),
        name="docs",
    ),
    # static files (*.css, *.js, *.jpg etc.)
    re_path(
        r"^(?!/?client/)(?P<path>.*\..*)$",
        RedirectView.as_view(url="/client/%(path)s", permanent=False),
        name="client",
    ),
]
