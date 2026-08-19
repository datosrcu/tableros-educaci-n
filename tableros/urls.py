from django.urls import path
from . import views

app_name = 'tableros'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('espacios-ludicos/', views.DashboardEspaciosLudicosView.as_view(), name='espacios_ludicos'),
    path('alfabetizacion/', views.DashboardAlfabetizacionView.as_view(), name='alfabetizacion'),
    path('carpinteria/', views.DashboardCarpinteriaView.as_view(), name='carpinteria'),
    path('artes-plasticas/', views.DashboardArtesPlasticasView.as_view(), name='artes_plasticas'),
    path('expresion-cultural/', views.DashboardExpresionCulturalView.as_view(), name='expresion_cultural'),
]
