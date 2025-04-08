import sqlite3
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Easy_Bill.settings')
django.setup()

from uibill.models import Transaction

# 连接旧数据库
old_conn = sqlite3.connect('0409backup.sqlite3')
old_cursor = old_conn.cursor()

# 查询旧数据
old_cursor.execute('SELECT transaction_date, amount, category_code, description, payment_method, order_number FROM uibill_transaction')
old_records = old_cursor.fetchall()

# 导入到新模型
for record in old_records:
    transaction_date, amount, category_code, description, payment_method, order_number = record
    
    # 创建新记录，设置tags为空字符串
    Transaction.objects.create(
        transaction_date=transaction_date,
        amount=amount,
        category_code=category_code,
        description=description,
        payment_method=payment_method,
        order_number=order_number or '',
        location='',
        is_recurring=False,
        notes='',
        tags=''  # 新字段设置默认值
    )

old_conn.close()
print("数据导入完成！")