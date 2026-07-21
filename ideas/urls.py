from django.urls import path

from ideas import views

urlpatterns = [
    path('quartz/', views.quartz, name='quartz'),
]