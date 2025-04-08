from django.db import models
from django.utils import timezone

class Transaction(models.Model):
    CATEGORY_CHOICES = [
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
        ('M', '娱乐'),
    ]

    PAYMENT_CHOICES = [
        ('WCP', '微信'),
        ('ZFB', '支付宝'),
        ('CSH', '现金'),
        ('JDP', '京东白条'),
        ('JTC', '交通信用卡'),
        ('NSC', '农商信用卡'),
        ('OTC', '储蓄银行卡'),
        ('MTP', '美团'),
    ]

    transaction_date = models.DateField(verbose_name='交易日期')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='金额')
    category_code = models.CharField(max_length=1, choices=CATEGORY_CHOICES, verbose_name='类别')
    description = models.CharField(max_length=200, verbose_name='描述')
    payment_method = models.CharField(max_length=3, choices=PAYMENT_CHOICES, verbose_name='支付方式')
    order_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='订单编号')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 新增字段
    tags = models.CharField(max_length=200, blank=True, null=True, verbose_name='标签')
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name='位置')
    is_recurring = models.BooleanField(default=False, verbose_name='是否为周期性支出')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')

    class Meta:
        verbose_name = '交易记录'
        verbose_name_plural = '交易记录'
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.get_category_code_display()} - ¥{self.amount} - {self.transaction_date}"
    
    @property
    def is_income(self):
        return self.category_code == 'L'
    
    @property
    def is_expense(self):
        return not self.is_income


class Budget(models.Model):
    PERIOD_CHOICES = [
        ('monthly', '每月'),
        ('yearly', '每年'),
    ]
    
    category_code = models.CharField(max_length=1, choices=Transaction.CATEGORY_CHOICES, verbose_name='类别')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='预算金额')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly', verbose_name='预算周期')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(blank=True, null=True, verbose_name='结束日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '预算'
        verbose_name_plural = '预算'
        
    def __str__(self):
        return f"{self.get_category_code_display()} - ¥{self.amount} ({self.get_period_display()})"
    
    def get_category_code_display(self):
        return dict(Transaction.CATEGORY_CHOICES).get(self.category_code, '')
    
    def get_spent_amount(self):
        """计算在预算周期内已经花费的金额"""
        if not self.start_date:
            return 0
            
        end = self.end_date or timezone.now().date()
        
        return Transaction.objects.filter(
            category_code=self.category_code,
            transaction_date__gte=self.start_date,
            transaction_date__lte=end
        ).exclude(
            category_code='L'  # 排除收入
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    def get_remaining_amount(self):
        """计算预算剩余金额"""
        spent = self.get_spent_amount()
        return self.amount - spent
    
    def get_percentage_used(self):
        """计算预算使用百分比"""
        if self.amount == 0:
            return 100
        
        spent = self.get_spent_amount()
        return min(100, round((spent / self.amount) * 100))