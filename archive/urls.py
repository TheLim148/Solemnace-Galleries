from django.urls import path

from . import views


app_name = "archive"

urlpatterns = [
    path("", views.home, name="home"),
    path("exhibits/", views.exhibit_list, name="exhibit_list"),
    path("exhibits/<int:pk>/", views.exhibit_detail, name="exhibit_detail"),
]
