from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'amount', 'get_category_display', 'description', 
                   'get_payment_display', 'order_number', 'created_at')
    list_filter = ('category_code', 'payment_method', 'transaction_date')
    search_fields = ('description', 'order_number')
    date_hierarchy = 'transaction_date'

    def get_category_display(self, obj):
        return obj.get_category_code_display()
    get_category_display.short_description = '类别'

    def get_payment_display(self, obj):
        return obj.get_payment_method_display()
    get_payment_display.short_description = '支付方式'