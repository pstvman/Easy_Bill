#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Easy_Bill.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # 如果是runserver命令且没有指定端口，则使用高端口并绑定到所有网络接口
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver' and len(sys.argv) == 2:
        sys.argv.append('0.0.0.0:18527')
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
