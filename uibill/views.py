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
from django.http import JsonResponse


def home(request):
    # 获取最近的10条记录
    recent_transactions = Transaction.objects.all().order_by('-transaction_date')[:10]
    
    # 获取当前月份的数据
    today = datetime.now().date()
    first_day_of_month = today.replace(day=1)
    
    # 计算本月支出
    monthly_expense = Transaction.objects.filter(
        transaction_date__gte=first_day_of_month,
        transaction_date__lte=today
    ).exclude(
        category_code='L'  # 排除收入类别
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # 计算本月收入
    monthly_income = Transaction.objects.filter(
        transaction_date__gte=first_day_of_month,
        transaction_date__lte=today,
        category_code='L'  # 只包括收入类别
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # 计算本月结余
    monthly_balance = monthly_income - monthly_expense
    
    # 从session获取上次的数据
    transaction_data = request.session.get('transaction_data', {})
    initial_data = {
        'transaction_date': transaction_data.get('transaction_date'),
        'category_code': transaction_data.get('category'),
        'payment_method': transaction_data.get('payment'),
    }
    form = TransactionForm(initial=initial_data)
    
    return render(request, 'home.html', {
        'form': form,
        'transaction_data': request.session.get('transaction_data', {}),
        'recent_transactions': recent_transactions,
        'monthly_expense': monthly_expense,
        'monthly_income': monthly_income,
        'monthly_balance': monthly_balance
    })

def add_transaction(request):
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
            
            if request.POST.get('continue') == 'true':
                return render(request, 'success.html', {'continue_recording': True})
            return render(request, 'success.html', {'continue_recording': False})

    else:
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

def success_view(request):
    # 如果是从iframe中访问的，返回success.html
    if request.META.get('HTTP_SEC_FETCH_DEST') == 'iframe':
        return render(request, 'success.html')
    # 否则重定向到主页
    return redirect('home')

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
            return redirect('home')  # 成功后重定向到主页
            
        except Exception as e:
            messages.error(request, f'导入失败：{str(e)}')
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
    
    # 处理排序
    sort = request.GET.get('sort', '-transaction_date')
    transactions = transactions.order_by(sort)
    
    # 处理筛选条件
    if form.is_valid():
        # 支付方式筛选
        if form.cleaned_data.get('payment_method'):
            transactions = transactions.filter(payment_method=form.cleaned_data['payment_method'])
        
        # 类别筛选
        if form.cleaned_data.get('category_code'):
            transactions = transactions.filter(category_code=form.cleaned_data['category_code'])
        
        # 日期范围筛选
        date_range = form.cleaned_data.get('date_range')
        if date_range:
            today = datetime.now().date()
            
            if date_range == '7days':
                start_date = today - timedelta(days=7)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == '15days':
                start_date = today - timedelta(days=15)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == 'this_month':
                start_date = today.replace(day=1)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == 'last_month':
                last_month = today.replace(day=1) - timedelta(days=1)
                start_date = last_month.replace(day=1)
                end_date = today.replace(day=1) - timedelta(days=1)
                transactions = transactions.filter(transaction_date__gte=start_date, transaction_date__lte=end_date)
            elif date_range == 'this_quarter':
                current_quarter = (today.month - 1) // 3 + 1
                start_date = today.replace(month=(current_quarter-1)*3+1, day=1)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == 'last_quarter':
                current_quarter = (today.month - 1) // 3 + 1
                if current_quarter == 1:
                    start_date = today.replace(year=today.year-1, month=10, day=1)
                    end_date = today.replace(year=today.year-1, month=12, day=31)
                else:
                    start_date = today.replace(month=((current_quarter-2)*3+1), day=1)
                    end_month = (current_quarter-1)*3
                    end_date = (today.replace(month=end_month+1, day=1) - timedelta(days=1))
                transactions = transactions.filter(transaction_date__gte=start_date, transaction_date__lte=end_date)
            elif date_range == 'this_year':
                start_date = today.replace(month=1, day=1)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == 'last_year':
                start_date = today.replace(year=today.year-1, month=1, day=1)
                end_date = today.replace(year=today.year-1, month=12, day=31)
                transactions = transactions.filter(transaction_date__gte=start_date, transaction_date__lte=end_date)
            elif date_range == 'custom':
                # 处理自定义日期范围
                start_date = form.cleaned_data.get('start_date')
                end_date = form.cleaned_data.get('end_date')
                if start_date:
                    transactions = transactions.filter(transaction_date__gte=start_date)
                if end_date:
                    transactions = transactions.filter(transaction_date__lte=end_date)
        
        # 金额范围筛选
        if form.cleaned_data.get('min_amount'):
            transactions = transactions.filter(amount__gte=form.cleaned_data['min_amount'])
        if form.cleaned_data.get('max_amount'):
            transactions = transactions.filter(amount__lte=form.cleaned_data['max_amount'])
        
        # 搜索条件
        if form.cleaned_data.get('search_term'):
            search_term = form.cleaned_data['search_term']
            transactions = transactions.filter(
                Q(description__icontains=search_term) | 
                Q(tags__icontains=search_term) | 
                Q(notes__icontains=search_term)
            )
    
    # 准备图表数据
    chart_data = prepare_chart_data(transactions)
    
    return render(request, 'query.html', {
        'form': form,
        'transactions': transactions,
        'chart_data_json': json.dumps(chart_data),
        'sort': sort
    })

def prepare_chart_data(transactions):
    # 类别分布数据
    category_data = {}
    for transaction in transactions:
        if transaction.category_code != 'L':  # 排除收入类别
            category = transaction.get_category_code_display()
            if category in category_data:
                category_data[category] += float(transaction.amount)
            else:
                category_data[category] = float(transaction.amount)
    
    # 按金额排序
    sorted_categories = sorted(category_data.items(), key=lambda x: x[1], reverse=True)
    category_labels = [item[0] for item in sorted_categories]
    category_values = [item[1] for item in sorted_categories]
    
    # 月度趋势数据
    monthly_data = {}
    income_monthly_data = {}
    
    for transaction in transactions:
        month_key = transaction.transaction_date.strftime('%Y-%m')
        
        if transaction.category_code == 'L':  # 收入
            if month_key in income_monthly_data:
                income_monthly_data[month_key] += float(transaction.amount)
            else:
                income_monthly_data[month_key] = float(transaction.amount)
        else:  # 支出
            if month_key in monthly_data:
                monthly_data[month_key] += float(transaction.amount)
            else:
                monthly_data[month_key] = float(transaction.amount)
    
    # 确保所有月份都有数据
    all_months = sorted(set(list(monthly_data.keys()) + list(income_monthly_data.keys())))
    
    monthly_labels = all_months
    expense_values = [monthly_data.get(month, 0) for month in all_months]
    income_values = [income_monthly_data.get(month, 0) for month in all_months]
    
    # 支付方式分布
    payment_data = {}
    for transaction in transactions:
        if transaction.category_code != 'L':  # 排除收入
            payment = transaction.get_payment_method_display()
            if payment in payment_data:
                payment_data[payment] += float(transaction.amount)
            else:
                payment_data[payment] = float(transaction.amount)
    
    # 按金额排序
    sorted_payments = sorted(payment_data.items(), key=lambda x: x[1], reverse=True)
    payment_labels = [item[0] for item in sorted_payments]
    payment_values = [item[1] for item in sorted_payments]
    
    return {
        'categories': {
            'labels': category_labels,
            'data': category_values
        },
        'monthly': {
            'labels': monthly_labels,
            'expense_data': expense_values,
            'income_data': income_values
        },
        'payments': {
            'labels': payment_labels,
            'data': payment_values
        }
    }

# 在views.py中添加预算相关视图

def budget_list(request):
    budgets = Budget.objects.all().order_by('category_code')
    
    # 计算每个预算的使用情况
    for budget in budgets:
        budget.spent = budget.get_spent_amount()
        budget.remaining = budget.get_remaining_amount()
        budget.percentage = budget.get_percentage_used()
    
    return render(request, 'budget_list.html', {
        'budgets': budgets
    })

def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '预算设置已保存！')
            return redirect('budget_list')
    else:
        form = BudgetForm()
    
    return render(request, 'budget_form.html', {
        'form': form,
        'title': '添加预算'
    })

def edit_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, '预算已更新！')
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget)
    
    return render(request, 'budget_form.html', {
        'form': form,
        'title': '编辑预算',
        'budget': budget
    })

def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, '预算已删除！')
        return redirect('budget_list')
    
    return render(request, 'confirm_delete.html', {
        'object': budget,
        'title': '删除预算'
    })


def export_transactions(request):
    """导出交易记录为Excel文件"""
    # 获取筛选后的交易记录
    form = TransactionQueryForm(request.GET)
    transactions = Transaction.objects.all()
    
    # 应用与查询相同的筛选条件
    if form.is_valid():
        # 支付方式筛选
        if form.cleaned_data.get('payment_method'):
            transactions = transactions.filter(payment_method=form.cleaned_data['payment_method'])
        
        # 类别筛选
        if form.cleaned_data.get('category_code'):
            transactions = transactions.filter(category_code=form.cleaned_data['category_code'])
        
        # 日期范围筛选
        date_range = form.cleaned_data.get('date_range')
        if date_range:
            today = datetime.now().date()
            
            if date_range == '7days':
                start_date = today - timedelta(days=7)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == '15days':
                start_date = today - timedelta(days=15)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == 'this_month':
                start_date = today.replace(day=1)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == 'last_month':
                last_month = today.replace(day=1) - timedelta(days=1)
                start_date = last_month.replace(day=1)
                end_date = today.replace(day=1) - timedelta(days=1)
                transactions = transactions.filter(transaction_date__gte=start_date, transaction_date__lte=end_date)
            elif date_range == 'this_quarter':
                current_quarter = (today.month - 1) // 3 + 1
                start_date = today.replace(month=(current_quarter-1)*3+1, day=1)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == 'last_quarter':
                current_quarter = (today.month - 1) // 3 + 1
                if current_quarter == 1:
                    start_date = today.replace(year=today.year-1, month=10, day=1)
                    end_date = today.replace(year=today.year-1, month=12, day=31)
                else:
                    start_date = today.replace(month=((current_quarter-2)*3+1), day=1)
                    end_month = (current_quarter-1)*3
                    end_date = (today.replace(month=end_month+1, day=1) - timedelta(days=1))
                transactions = transactions.filter(transaction_date__gte=start_date, transaction_date__lte=end_date)
            elif date_range == 'this_year':
                start_date = today.replace(month=1, day=1)
                transactions = transactions.filter(transaction_date__gte=start_date)
            elif date_range == 'last_year':
                start_date = today.replace(year=today.year-1, month=1, day=1)
                end_date = today.replace(year=today.year-1, month=12, day=31)
                transactions = transactions.filter(transaction_date__gte=start_date, transaction_date__lte=end_date)
            elif date_range == 'custom':
                # 处理自定义日期范围
                start_date = form.cleaned_data.get('start_date')
                end_date = form.cleaned_data.get('end_date')
                if start_date:
                    transactions = transactions.filter(transaction_date__gte=start_date)
                if end_date:
                    transactions = transactions.filter(transaction_date__lte=end_date)
        
        # 金额范围筛选
        if form.cleaned_data.get('min_amount'):
            transactions = transactions.filter(amount__gte=form.cleaned_data['min_amount'])
        if form.cleaned_data.get('max_amount'):
            transactions = transactions.filter(amount__lte=form.cleaned_data['max_amount'])
        
        # 搜索条件
        if form.cleaned_data.get('search_term'):
            search_term = form.cleaned_data['search_term']
            transactions = transactions.filter(
                Q(description__icontains=search_term) | 
                Q(tags__icontains=search_term) | 
                Q(notes__icontains=search_term)
            )
    
    # 创建DataFrame
    data = []
    for t in transactions:
        data.append({
            '交易日期': t.transaction_date,
            '金额': t.amount,
            '类别': t.get_category_code_display(),
            '类别代码': t.category_code,
            '描述': t.description,
            '支付方式': t.get_payment_method_display(),
            '支付方式代码': t.payment_method,
            '订单编号': t.order_number,
            '标签': t.tags,
            '位置': t.location,
            '周期性': '是' if t.is_recurring else '否',
            '备注': t.notes
        })
    
    df = pd.DataFrame(data)
    
    # 创建响应
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=transactions.xlsx'
    
    # 写入Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='交易记录')
        
        # 获取工作表
        worksheet = writer.sheets['交易记录']
        
        # 调整列宽
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_len
    
    return response

def download_template(request):
    """下载Excel导入模板"""
    # 创建示例数据
    data = [
        {
            'transaction_date': datetime.now().date(),
            'amount': 100.00,
            'category_code': 'A',
            'description': '超市购物',
            'payment_method': 'WCP',
            'order_number': '2023ABCD1234',
            'tags': '日常,食品',
            'location': '家乐福超市',
            'is_recurring': False,
            'notes': '周末采购'
        },
        {
            'transaction_date': datetime.now().date(),
            'amount': 200.00,
            'category_code': 'B',
            'description': '晚餐',
            'payment_method': 'ZFB',
            'order_number': '',
            'tags': '聚餐,朋友',
            'location': '海底捞',
            'is_recurring': False,
            'notes': '朋友聚会'
        },
        {
            'transaction_date': datetime.now().date(),
            'amount': 1500.00,
            'category_code': 'L',
            'description': '工资',
            'payment_method': 'OTC',
            'order_number': '',
            'tags': '收入,工资',
            'location': '',
            'is_recurring': True,
            'notes': '每月工资'
        }
    ]
    
    df = pd.DataFrame(data)
    
    # 创建响应
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=transaction_template.xlsx'
    
    # 写入Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='导入模板')
        
        # 获取工作表
        worksheet = writer.sheets['导入模板']
        
        # 添加说明工作表
        workbook = writer.book
        instructions = workbook.create_sheet('使用说明')
        
        # 添加说明内容
        instructions['A1'] = '字段说明'
        instructions['A2'] = 'transaction_date: 交易日期，格式为YYYY-MM-DD'
        instructions['A3'] = 'amount: 金额，数字格式'
        instructions['A4'] = 'category_code: 类别代码，参考下方类别代码表'
        instructions['A5'] = 'description: 交易描述'
        instructions['A6'] = 'payment_method: 支付方式代码，参考下方支付方式代码表'
        instructions['A7'] = 'order_number: 订单编号（可选）'
        instructions['A8'] = 'tags: 标签，多个标签用逗号分隔（可选）'
        instructions['A9'] = 'location: 交易地点（可选）'
        instructions['A10'] = 'is_recurring: 是否为周期性交易，True或False（可选）'
        instructions['A11'] = 'notes: 备注（可选）'
        
        instructions['A13'] = '类别代码表'
        for i, (code, name) in enumerate(Transaction.CATEGORY_CHOICES):
            instructions[f'A{14+i}'] = f'{code}: {name}'
        
        instructions['C13'] = '支付方式代码表'
        for i, (code, name) in enumerate(Transaction.PAYMENT_CHOICES):
            instructions[f'C{14+i}'] = f'{code}: {name}'
        
        # 调整列宽
        for col in ['A', 'C']:
            instructions.column_dimensions[col].width = 40
    
    return response

def backup_restore(request):
    """备份和恢复数据页面"""
    return render(request, 'backup_restore.html')

def backup_data(request):
    """备份所有数据到JSON文件"""
    # 获取所有交易记录
    transactions = Transaction.objects.all()
    transaction_data = []
    
    for t in transactions:
        transaction_data.append({
            'transaction_date': t.transaction_date.isoformat(),
            'amount': str(t.amount),
            'category_code': t.category_code,
            'description': t.description,
            'payment_method': t.payment_method,
            'order_number': t.order_number,
            'tags': t.tags,
            'location': t.location,
            'is_recurring': t.is_recurring,
            'notes': t.notes,
        })
    
    # 获取所有预算
    budgets = Budget.objects.all()
    budget_data = []
    
    for b in budgets:
        budget_data.append({
            'category_code': b.category_code,
            'amount': str(b.amount),
            'period': b.period,
            'start_date': b.start_date.isoformat(),
            'end_date': b.end_date.isoformat() if b.end_date else None,
        })
    
    # 创建完整的备份数据
    backup = {
        'transactions': transaction_data,
        'budgets': budget_data,
        'backup_date': timezone.now().isoformat(),
        'version': '1.0'
    }
    
    # 创建响应
    response = HttpResponse(
        json.dumps(backup, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename=easy_bill_backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    return response

@transaction.atomic
def restore_data(request):
    """从JSON文件恢复数据"""
    if request.method != 'POST' or 'backup_file' not in request.FILES:
        messages.error(request, '请选择备份文件')
        return redirect('backup_restore')
    
    backup_file = request.FILES['backup_file']
    
    try:
        # 读取JSON数据
        backup_data = json.loads(backup_file.read().decode('utf-8'))
        
        # 验证备份文件格式
        if 'transactions' not in backup_data or 'budgets' not in backup_data:
            messages.error(request, '无效的备份文件格式')
            return redirect('backup_restore')
        
        # 如果选择了清除现有数据
        if request.POST.get('clear_existing') == 'yes':
            Transaction.objects.all().delete()
            Budget.objects.all().delete()
        
        # 恢复交易记录
        for t_data in backup_data['transactions']:
            Transaction.objects.create(
                transaction_date=datetime.fromisoformat(t_data['transaction_date']),
                amount=t_data['amount'],
                category_code=t_data['category_code'],
                description=t_data['description'],
                payment_method=t_data['payment_method'],
                order_number=t_data.get('order_number', ''),
                tags=t_data.get('tags', ''),
                location=t_data.get('location', ''),
                is_recurring=t_data.get('is_recurring', False),
                notes=t_data.get('notes', ''),
            )
        
        # 恢复预算
        for b_data in backup_data['budgets']:
            Budget.objects.create(
                category_code=b_data['category_code'],
                amount=b_data['amount'],
                period=b_data['period'],
                start_date=datetime.fromisoformat(b_data['start_date']),
                end_date=datetime.fromisoformat(b_data['end_date']) if b_data['end_date'] else None,
            )
        
        messages.success(request, f'成功恢复数据！共恢复{len(backup_data["transactions"])}条交易记录和{len(backup_data["budgets"])}条预算记录。')
        
    except json.JSONDecodeError:
        messages.error(request, '无法解析备份文件，请确保文件格式正确')
    except Exception as e:
        messages.error(request, f'恢复数据时出错: {str(e)}')
    
    return redirect('backup_restore')
