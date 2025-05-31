@echo off
chcp 65001

:: 设置环境名称
set ENV_NAME=easy-bill

:: 激活环境
call conda activate %ENV_NAME%

:: 确认环境激活状态
echo current python env:
call conda info --envs
echo current python path:
where python

:: 设置项目路径
::cd /d D:\project\xx

:: 运行项目
echo 正在启动 Easy-Bill 项目...
python manage.py runserver 127.0.0.1:18527

:: 如果程序异常退出，暂停显示错误信息
if errorlevel 1 (
    echo 程序异常退出！
    pause
)