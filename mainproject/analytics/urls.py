from django.urls import path
from . import views

urlpatterns = [
    path('', views.vendor_list_view, name='vendor_list'),
    path('active/', views.active_vendors_view, name='active_vendors'),
    path('logged-in/', views.logged_in_vendors_view, name='logged_in_vendors'),
    path('new/week/', views.new_vendors_week_view, name='new_vendors_week'),
    path('/new/month/', views.new_vendors_month_view, name='new_vendors_month'),
    path('dau/', views.dau_view, name='dau_vendors'),
    path('wau/', views.wau_view, name='wau_vendors'),
    path('mau/', views.mau_view, name='mau_vendors'),
    path('dormant/', views.dormant_vendors_view, name='dormant_vendors'),
    path('avg-session/', views.avg_session_view, name='avg_session_vendors'),
]
