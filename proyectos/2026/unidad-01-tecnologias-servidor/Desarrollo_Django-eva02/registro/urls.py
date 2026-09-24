from django.urls import path

from . import views

urlpatterns = [
    path('', views.ListaMichisView.as_view(), name='lista_michis'),
    path('agregar/', views.AgregarMichiView.as_view(), name='agregar_michi'),
    path('<int:pk>/', views.DetalleMichiView.as_view(), name='detalle_michi'),
    path('<int:pk>/editar/', views.EditarMichiView.as_view(), name='editar_michi'),
    path('<int:pk>/eliminar/', views.MichiDeleteView.as_view(), name='eliminar_michi'),
]
