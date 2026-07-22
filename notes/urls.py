from django.urls import path

from notes import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),
    path('notes/<int:pk>/export/', views.export_note_md, name='note_download'),
    path('graph/', views.quartz, name='quartz'),
    path('graph/data/', views.graph_data, name='graph_data'),
]