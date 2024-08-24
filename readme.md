tips

- pyinstaller -w -F ./main.pyw -p <virtual_env_dir_path>  // 打包命令 -p 指定虚拟环境的文件夹路径
- python==3.10.6 pyinstaller==5.10.1

info

- 在window上运行的用于提醒的小程序
- 需要停止, 运行参数增加 stop 或者在__task__.json中增加一个项目为{"func":"stop"}

issue

- *.pyw 不显示占用的终端
- windows taskschd.msc 定时任务计划
  - 只在用户登录时运行 才或有图形界面，否则会堵塞
  - 操作选项 起始于 默认为c:\windows\system32 即应用程序在 指定目录下运行，python的相对路径都起始于它

tasks structure

```json
[
  {
    "cron": "* * * * *",
    "type": "success",
    "title": "提醒",
    "content": "一切有解，是否愿解？"
  }
]
```
