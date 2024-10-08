# satori-balance-checker
satori批量余额检查脚本
**当前脚本只能查询同一个IP上部署的服务**
**配合Z大的批量安装脚本使用 [地址](https://medium.com/@zephyrsailor0715/satori多节点管理-优化部署-提升效率-c1d62fa5c00c)**

# 使用方式
## 安装依赖
```shell
git clone https://github.com/CCCCCCoder/satori-balance-checker.git
cd satori-balance-checker
pip install -r requirements.txt
```
## 批量查询余额

### 推荐使用新的脚本，从dashboard获取余额，速度更快
```
python3 checkBalanceFromDashboard.py
```
## 批量修改归集地址
```
python3 SetRewardAddress.py
```

### 归集satori

```shell
python3 CollectionAllBalance.py
```

# 配置文件说明
```ini
[server]
ip = 10.xxx.xxx.xxx #服务器IP
start_port = 24601 #起始端口号
num_ports = 10 #节点数
password_consistent = true #是否统一密码，如果所有节点的密码一致，则这里填true
password = password # 密码

balanceThreshold = 5 #余额阈值，低于此值会被归集 默认5，五颗以上的节点不会被归集
collectAddress = ETjntV3TAYAqcd65LE5jT7ByUYVy7FAfsK #归集地址

[passwords]
24601 = password # 当不是统一密码时，在这里填入每个端口号对应的密码
24602 = anotherPassword
24603 = yetAnotherPassword
```

# 脚本逻辑

# 查询余额
首先直接对IP+PORT发起请求，如果satori加锁，此时会返回302重定向，调用密码进行解锁
解锁后从dom中提取csrf token和cookie
如果未加锁，会直接获取到页面的html，提取csrf token和cookie

随后访问vault/dashboard，从html的dom元素中解析出余额

# 批量归集

首先查询所有节点的余额，如果余额大于阈值，则不进行归集
如果余额小于阈值，则调用归集接口，将余额归集到指定地址
