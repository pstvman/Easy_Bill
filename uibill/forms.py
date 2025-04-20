from django import forms
from datetime import datetime, timedelta
from .models import Transaction, Budget

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_date', 'amount', 'category_code', 'description', 
                 'payment_method', 'order_number', 'tags', 'location', 'is_recurring', 'notes']
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category_code': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'order_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '多个标签用逗号分隔'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TransactionQueryForm(forms.Form):
    PAYMENT_CHOICES = [('', '所有')] + list(Transaction.PAYMENT_CHOICES)
    CATEGORY_CHOICES = [('', '所有')] + list(Transaction.CATEGORY_CHOICES)
    
    DATE_RANGE_CHOICES = [
        ('', '所有日期'),
        ('7days', '最近7天'),
        ('15days', '最近15天'),
        ('this_month', '本月'),
        ('last_month', '上月'),
        ('this_quarter', '本季度'),
        ('last_quarter', '上季度'),
        ('this_year', '今年'),
        ('last_year', '去年'),
        ('custom', '自定义范围'),
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
        label='时间范围',
        initial='this_year'
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='开始日期'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='结束日期'
    )
    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='最小金额'
    )
    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='最大金额'
    )
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '搜索描述、标签或备注'}),
        label='搜索'
    )

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category_code', 'amount', 'period', 'start_date', 'end_date']
        widgets = {
            'category_code': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }