from django.db import models

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
    ]

    PAYMENT_CHOICES = [
        ('1', '微信'),
        ('2', '支付宝'),
        ('3', '现金'),
        ('4', '京东白条'),
        ('5', '交通银行信用卡'),
        ('6', '农商行信用卡'),
        ('7', '其他银行卡'),
    ]

    transaction_date = models.DateField(verbose_name='交易日期')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='金额')
    category_code = models.CharField(max_length=1, choices=CATEGORY_CHOICES, verbose_name='类别')
    description = models.CharField(max_length=200, verbose_name='描述')
    payment_method = models.CharField(max_length=1, choices=PAYMENT_CHOICES, verbose_name='支付方式')
    order_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='订单编号')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '交易记录'
        verbose_name_plural = '交易记录'

    def __str__(self):
        return f"{self.get_category_code_display()} - ¥{self.amount} - {self.transaction_date}"