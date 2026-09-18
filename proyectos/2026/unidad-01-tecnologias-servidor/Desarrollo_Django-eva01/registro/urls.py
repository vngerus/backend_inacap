from django.urls import path

from . import views

urlpatterns = [
    path('', views.ListaMichisView.as_view(), name='lista_michis'),
    path('agregar/', views.agregar_michi, name='agregar_michi'),
    path('<int:pk>/', views.DetalleMichiView.as_view(), name='detalle_michi'),
    path('<int:pk>/editar/', views.editar_michi, name='editar_michi'),
]
