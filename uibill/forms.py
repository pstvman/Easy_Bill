from django import forms
from datetime import datetime, timedelta
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_date', 'amount', 'category_code', 'description', 'payment_method', 'order_number']
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category_code': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'order_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TransactionQueryForm(forms.Form):
    PAYMENT_CHOICES = [('', '所有')] + [
        ('1', '微信'),
        ('2', '支付宝'),
        ('3', '现金'),
        ('4', '京东白条'),
        ('5', '交通银行信用卡'),
        ('6', '农商行信用卡'),
        ('7', '其他银行卡'),
    ]
    
    CATEGORY_CHOICES = [('', '所有')] + [
        ('A', '生活'),
        ('B', '聚餐'),
        ('C', '烟酒'),
        ('D', '用品'),
        ('E', '穿搭'),
        ('F', '房租'),
        ('G', '水费'),
        ('H', '电费'),
        ('I', '网费'),
        ('J', '出行'),
        ('K', '投资'),
        ('L', '收入'),
    ]
    
    DATE_RANGE_CHOICES = [
        ('', '选择时间范围'),
        ('7days', '最近7天'),
        ('15days', '最近15天'),
        ('this_month', '本月'),
        ('last_month', '上月'),
        ('this_quarter', '本季度'),
        ('last_quarter', '上季度'),
        ('this_year', '今年'),
        ('last_year', '去年'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES, 
        required=False,
        label='支付方式'
    )
    category_code = forms.ChoiceField(
        choices=CATEGORY_CHOICES, 
        required=False,
        label='类别'
    )
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        required=False,
        label='时间范围'
    )