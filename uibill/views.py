import pandas as pd
import json
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Transaction
from .forms import TransactionForm, TransactionQueryForm


def my_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save()
            messages.success(request, '交易记录已成功保存！')

            # 保存上一次提交的数据到session
            request.session['transaction_data'] = {
                'transaction_date': request.POST.get('transaction_date'),
                'category': request.POST.get('category_code'),
                'payment': request.POST.get('payment_method'),
            }

            return redirect('success')
    else:
        # 从session获取上次的数据
        transaction_data = request.session.get('transaction_data', {})
        initial_data = {
            'transaction_date': transaction_data.get('transaction_date'),
            'category_code': transaction_data.get('category'),
            'payment_method': transaction_data.get('payment'),
        }
        form = TransactionForm(initial=initial_data)
    return render(request, 'record.html', {
        'form': form,
        'transaction_data': request.session.get('transaction_data', {})
        })

def home(request):
    return render(request, 'home.html')

# 表格提交成功后执行的跳转
def success_view(request):
    return render(request, 'success.html')

def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file)
            
            # 数据预处理
            # 1. 处理日期
            df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.date
            
            # 2. 处理空值
            df = df.fillna({
                'amount': 0,
                'category_code': '',
                'description': '',
                'payment_method': '',
                'order_number': ''
            })
            
            # 3. 确保金额为数字类型
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
            # 开始批量导入
            with transaction.atomic():
                for _, row in df.iterrows():
                    # 跳过金额为空或0的行
                    if pd.isna(row['amount']) or row['amount'] == 0:
                        continue
                        
                    Transaction.objects.create(
                        transaction_date=row['transaction_date'],
                        amount=row['amount'],
                        category_code=row['category_code'],
                        description=row['description'],
                        payment_method=row['payment_method'],
                        order_number=row['order_number'] if pd.notna(row['order_number']) else None
                    )
            
            messages.success(request, f'成功导入 {len(df)} 条记录！')
            
        except Exception as e:
            messages.error(request, f'导入失败：{str(e)}')
            # 添加详细的错误日志
            print(f"导入错误详情: {str(e)}")
            
    return render(request, 'import_excel.html')

def download_template(request):
    # 创建示例数据
    data = {
        'transaction_date': ['2024-04-17'],
        'amount': [500.00],
        'category_code': ['A'],
        'description': ['酒店消费'],
        'payment_method': ['1'],
        'order_number': ['zf-20240417']
    }
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建响应
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=transaction_template.xlsx'
    
    # 保存到响应
    df.to_excel(response, index=False)
    return response

def query_transactions(request):
    form = TransactionQueryForm(request.GET)
    transactions = Transaction.objects.all()
    
    # 获取排序参数
    sort = request.GET.get('sort', '-transaction_date')  # 默认按日期降序

    if form.is_valid():
        # 支付方式过滤
        if form.cleaned_data['payment_method']:
            transactions = transactions.filter(
                payment_method=form.cleaned_data['payment_method']
            )
        
        # 类别过滤
        if form.cleaned_data['category_code']:
            transactions = transactions.filter(
                category_code=form.cleaned_data['category_code']
            )
        
        # 日期范围过滤
        date_range = form.cleaned_data['date_range']
        today = datetime.now().date()
        
        if date_range:
            if date_range == '7days':
                start_date = today - timedelta(days=7)
                transactions = transactions.filter(transaction_date__gte=start_date)
            
            elif date_range == '15days':
                start_date = today - timedelta(days=15)
                transactions = transactions.filter(transaction_date__gte=start_date)
            
            elif date_range == 'this_month':
                transactions = transactions.filter(
                    transaction_date__year=today.year,
                    transaction_date__month=today.month
                )
            
            elif date_range == 'last_month':
                last_month = today - relativedelta(months=1)
                transactions = transactions.filter(
                    transaction_date__year=last_month.year,
                    transaction_date__month=last_month.month
                )
            
            elif date_range == 'this_quarter':
                quarter_start = today - timedelta(days=today.day - 1)
                quarter_start = quarter_start.replace(month=((today.month - 1) // 3) * 3 + 1)
                transactions = transactions.filter(transaction_date__gte=quarter_start)
            
            elif date_range == 'last_quarter':
                last_quarter_end = today.replace(day=1) - timedelta(days=1)
                last_quarter_start = last_quarter_end.replace(month=((last_quarter_end.month - 1) // 3) * 3 + 1, day=1)
                transactions = transactions.filter(
                    transaction_date__gte=last_quarter_start,
                    transaction_date__lte=last_quarter_end
                )
            
            elif date_range == 'this_year':
                transactions = transactions.filter(transaction_date__year=today.year)
            
            elif date_range == 'last_year':
                transactions = transactions.filter(transaction_date__year=today.year - 1)
        # 添加排序
        transactions = transactions.order_by(sort)

    # 准备图表数据
    # 1. 按类别统计支出
    category_data = transactions.exclude(category_code='L').values('category_code').annotate(
        total=Sum('amount')
    ).order_by('category_code')

    # 2. 按月份统计
    monthly_data = transactions.annotate(
        month=TruncMonth('transaction_date')
    ).values('month').annotate(
        expense=Sum('amount', filter=~Q(category_code='L')),
        income=Sum('amount', filter=Q(category_code='L'))
    ).order_by('month')

    # 转换为图表所需格式
    chart_data = {
        'categories': {
            'labels': [dict(Transaction.CATEGORY_CHOICES).get(item['category_code'], '') for item in category_data],
            'data': [abs(float(item['total'])) for item in category_data]
        },
        'monthly': {
            'labels': [item['month'].strftime('%Y-%m') for item in monthly_data],
            'expense_data': [abs(float(item['expense'] or 0)) for item in monthly_data],
            'income_data': [float(item['income'] or 0) for item in monthly_data]
        }
    }
    
    context = {
        'form': form,
        'transactions': transactions,
        'chart_data_json': json.dumps(chart_data),
        'sort': sort
    }
    
    return render(request, 'query.html', context)
