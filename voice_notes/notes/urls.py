from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('transcribe/', views.transcribe, name='transcribe'),
    path('save_text/', views.save_text, name='save_text'),
    path('resources/add/', views.add_resource, name='add_resource'),
    path('resources/download/<int:resource_id>/', views.download_resource, name='download_resource'),
    path('resources/<int:resource_id>/qa/', views.resource_qa, name='resource_qa'),
    path('export/txt/<int:note_id>/', views.export_text, name='export_text'),
    path('export/pdf/<int:note_id>/', views.export_pdf, name='export_pdf'),
]
