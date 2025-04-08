from django.contrib import admin
from django.urls import path
from uibill import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('success/', views.success_view, name='success'),
    path('import/', views.import_excel, name='import_excel'),
    path('download-template/', views.download_template, name='download_template'),
    path('query/', views.query_transactions, name='query_transactions'),
    path('export/', views.export_transactions, name='export_transactions'),
    
    # 预算管理
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/add/', views.add_budget, name='add_budget'),
    path('budgets/<int:pk>/edit/', views.edit_budget, name='edit_budget'),
    path('budgets/<int:pk>/delete/', views.delete_budget, name='delete_budget'),
    
    # 数据备份与恢复
    path('backup-restore/', views.backup_restore, name='backup_restore'),
    path('backup-data/', views.backup_data, name='backup_data'),
    path('restore-data/', views.restore_data, name='restore_data'),
]

