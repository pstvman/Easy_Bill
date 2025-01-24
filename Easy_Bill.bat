@echo off
chcp 65001
echo 正在启动项目...

:: 设置环境名称
set ENV_NAME=easy-bill

:: 激活环境
call conda activate %ENV_NAME%

:: 设置项目路径
::cd /d D:\project\xx

:: 运行项目
echo 启动 Flask 应用...
python manage.py runserver

:: 如果程序异常退出，暂停显示错误信息
if errorlevel 1 (
    echo 程序异常退出！
    pause
)