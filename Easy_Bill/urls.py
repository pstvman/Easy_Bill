from django.contrib import admin
from django.urls import path
from uibill.views import my_view, home, success_view
from uibill.views import import_excel, download_template
from uibill.views import query_transactions


urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', home, name='home'),
    path('', my_view, name='my_form'),
    path('success/', success_view, name='success'),
    path('import/', import_excel, name='import_excel'),
    path('download-template/', download_template, name='download_template'),
    path('query/', query_transactions, name='query_transactions'),
]

