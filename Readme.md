### 镜客居 签到脚本

---
#### 注意
因月曦论坛`bbs.wccc.cc`已迁移到镜客居`www.jkju.cc`，因此原先月曦论坛的签到脚本将会归档， 另开此仓库。

#### 免责声明
本文件仅供学习和技术交流使用，不得用于非法用途。对于因滥用而导致的任何法律责任，本人概不负责。

#### 环境要求:
    requests
    beautifulsoup4

#### 使用说明
1. 修改main.py的最后的 `if__name__=="__main__":` 函数:
替换其中的 `用户名/邮箱` 和 `密码`
```python
if __name__ == "__main__":
    # 用户名-密码登录
    AutoSign("用户名", "密码").start()
    # 邮箱-密码登录
    AutoSign("邮箱", "密码", is_email = True).start()
```
