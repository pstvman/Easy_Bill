# Easy Bill - 简易记账系统

Easy Bill是一个简单易用的个人记账系统，帮助您跟踪日常收支，管理预算，并提供数据分析功能。

## 功能特点

- 交易记录管理：添加、查询、导出交易记录
- 预算管理：设置不同类别的预算，跟踪支出情况
- 数据导入导出：支持Excel格式的数据导入和导出
- 数据备份与恢复：保护您的财务数据安全
- 数据分析：查看月度收支统计和趋势

## 安装与运行

### 环境要求

- Python 3.8+
- Django 5.1.4
- pandas 2.2.3
- openpyxl 3.1.5

### 安装依赖

```bash
pip install -r requrements.txt
```

# 启动服务
```bash
python manage.py runserver
```

# 访问后台管理
```bash
# admin/123456
http://localhost:8000/admin/
```