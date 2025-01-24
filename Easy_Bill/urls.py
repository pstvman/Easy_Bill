from django.contrib import admin
from django.urls import path
from uibill.views import (
    home, add_transaction, success_view, 
    import_excel, download_template, query_transactions
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('add/', add_transaction, name='add_transaction'),
    path('success/', success_view, name='success'),
    path('import/', import_excel, name='import_excel'),
    path('download-template/', download_template, name='download_template'),
    path('query/', query_transactions, name='query_transactions'),
]

