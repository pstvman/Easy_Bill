from django.contrib import admin
from .models import Transaction, Budget

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'amount', 'get_category_display', 'description', 
                   'get_payment_display', 'order_number', 'created_at')
    list_filter = ('category_code', 'payment_method', 'transaction_date', 'is_recurring')
    search_fields = ('description', 'order_number', 'tags', 'notes')
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('transaction_date', 'amount', 'category_code', 'description')
        }),
        ('支付信息', {
            'fields': ('payment_method', 'order_number')
        }),
        ('附加信息', {
            'fields': ('tags', 'location', 'is_recurring', 'notes')
        }),
    )

    def get_category_display(self, obj):
        return obj.get_category_code_display()
    get_category_display.short_description = '类别'

    def get_payment_display(self, obj):
        return obj.get_payment_method_display()
    get_payment_display.short_description = '支付方式'

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('get_category_display', 'amount', 'get_period_display', 
                   'start_date', 'end_date', 'get_spent_amount', 'get_remaining_amount', 'get_percentage_used')
    list_filter = ('period', 'category_code')
    
    def get_category_display(self, obj):
        return obj.get_category_code_display()
    get_category_display.short_description = '类别'