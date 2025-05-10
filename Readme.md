### 镜客居 签到脚本

---
#### 注意
因月曦论坛`bbs.wccc.cc`已迁移到镜客居`www.jkju.cc`，因此原先月曦论坛的签到脚本将会归档， 另开此仓库。

#### 免责声明
本文件仅供学习和技术交流使用，不得用于非法用途。对于因滥用而导致的任何法律责任，本人概不负责。

#### 使用说明
1. 直接运行
```shell
    # 进入main.py所在目录
    
    # 安装依赖库
    pip install -r requirements.txt
    
    # 命令行运行
    python main.py -u "用户" -p "密码" -m "登录方式"
    
    # 示例1 用户名-密码
    python main.py -u "用户名" -p "密码"
    
    # 示例2 邮箱-密码
    python main.py -u "邮箱" -p "密码" -m "email"
```
