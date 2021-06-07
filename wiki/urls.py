from django.urls import path

from . import views

app_name = 'wiki'
urlpatterns = [
    #path('', views.wiki, name="index"),
    path('wiki', views.wiki, name="wiki"), # just testing
]
