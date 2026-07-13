# 一键联网

本文介绍使用 `dji-qmi-network` 在 Linux 上完成 QMI 诊断、拨号、地址配置、路由和 DNS 管理。

## 1. 工作流程

```text
DJI 4G 模块
    │ USB
    ▼
option + qmi_wwan + cdc_wdm
    │
    ├── /dev/ttyUSB*      AT 串口
    ├── /dev/cdc-wdm0     QMI 控制设备
    └── wwp*/wwan*/wwx*   数据接口
            │
            ▼
      SIM 与 LTE 驻网
            │
            ▼
       WDS 数据会话
            │
            ▼
 IPv4 / 网关 / DNS / MTU
            │
            ▼
        Linux 网络
```

工具的连接时序：

```text
检测设备 → 处理 ModemManager → 启用 Raw-IP
→ 检查 SIM → 检查 LTE 注册与 PS 附着
→ 建立 WDS 会话 → 读取运营商参数
→ 配置地址 → 配置路由 → 配置 DNS
→ 测试连通性 → 保存运行状态
```

## 2. 运行诊断

```bash
sudo dji-qmi-network doctor
```

诊断内容包括：

- `qmicli`、`ip` 是否安装。
- `/dev/cdc-wdm*` 是否存在。
- 对应 WWAN 接口是否存在。
- QMI Raw-IP 是否为 `Y`。
- QMI 控制通道能否读取模块型号。
- SIM 是否就绪。
- LTE 是否已注册。
- PS 数据业务是否已附着。
- `ModemManager` 是否正在占用设备。

典型成功输出：

```text
✓ 命令 qmicli     已安装
✓ 命令 ip         已安装
✓ QMI 设备       /dev/cdc-wdm0
✓ 网络接口       wwp0s20f0u6i4
✓ Raw-IP         Y
✓ QMI 通信       QUECTEL Mobile Broadband Module
✓ SIM 卡         已就绪
✓ LTE 网络       registered=True, attached=True
✓ ModemManager   未占用
诊断完成：关键项目正常。
```

## 3. 一键连接

中国电信：

```bash
sudo dji-qmi-network connect --apn ctnet
```

中国移动：

```bash
sudo dji-qmi-network connect --apn cmnet
```

中国联通：

```bash
sudo dji-qmi-network connect --apn 3gnet
```

物联网卡请填写卡商提供的 APN。

连接成功后会显示：

```text
QMI 联网成功：
  设备：      /dev/cdc-wdm0
  接口：      wwp0s20f0u6i4
  APN：       ctnet
  IPv4：      10.5.30.188/29
  网关：      10.5.30.189
  DNS：       202.96.128.86, 202.96.134.133
  路由 metric：50
  连通性：    正常
  公网出口：  183.46.67.30
```

运营商分配的内网地址和公网出口地址可能随每次连接变化。

## 4. connect 实际做了什么

### 处理 ModemManager

Ubuntu 的 `ModemManager` 可能先占用 QMI 控制通道，造成：

```text
CID allocation failed in the CTL client: endpoint hangup
```

工具会在需要时自动停止它，并记录是否由本次连接停止，以便断开时恢复。

### 启用 Raw-IP

QDC507 实测使用 QMI Raw-IP：

```text
/sys/class/net/<接口>/qmi/raw_ip
```

目标值为：

```text
Y
```

### 建立 WDS 会话

工具调用 QMI WDS 服务，取得：

- CID：WDS 客户端 ID
- PDH：Packet Data Handle

这两个值会用于准确停止本次数据会话。

### 配置 Linux 网络

`qmi-network` 或 `qmicli --wds-start-network` 只代表蜂窝数据会话建立成功，不一定会为 Linux 接口配置 IPv4。

本工具会继续读取：

```bash
qmicli --wds-get-current-settings
```

并自动设置：

- IPv4 地址和前缀
- 接口 MTU
- 到网关的链路路由
- 默认路由
- systemd-resolved 链路 DNS

因此不依赖 `udhcpc`。

## 5. 默认路由 metric

默认使用：

```text
metric 50
```

数字越小，路由优先级越高。若有线网络 metric 为 `100`，4G 的 `50` 通常会成为默认出口。

让 4G 只作为备用线路：

```bash
sudo dji-qmi-network connect --apn ctnet --metric 500
```

查看当前路由：

```bash
ip route
```

指定 4G 接口测试，不受系统默认路由影响：

```bash
ping -I wwp0s20f0u6i4 -c 4 223.5.5.5
curl --interface wwp0s20f0u6i4 https://ifconfig.me
```

## 6. 查看状态

```bash
sudo dji-qmi-network status
```

典型输出：

```text
QMI 设备：/dev/cdc-wdm0
网络接口：wwp0s20f0u6i4
ModemManager：未运行
网络注册：已注册
数据附着：已附着
IPv4 地址：10.5.30.188/29
状态文件：/run/dji-qmi-network.json
APN：ctnet
CID/PDH：6/2263814208
```

状态文件：

```text
/run/dji-qmi-network.json
```

其中保存本次连接的设备、接口、APN、CID、PDH、地址、网关、DNS 和路由信息。

## 7. 断开连接

```bash
sudo dji-qmi-network disconnect
```

断开时会：

1. 使用保存的 CID 和 PDH 停止 WDS 会话。
2. 删除本工具添加的默认路由。
3. 清理接口 IPv4 地址。
4. 恢复链路 DNS 设置。
5. 删除运行状态文件。
6. 按需恢复连接前被停止的 `ModemManager`。

不恢复 ModemManager：

```bash
sudo dji-qmi-network disconnect --no-restore-modemmanager
```

## 8. 多设备和多接口

若系统存在多个 `/dev/cdc-wdm*` 或多个 WWAN 接口，应明确指定：

```bash
sudo dji-qmi-network \
  --device /dev/cdc-wdm0 \
  --interface wwp0s20f0u6i4 \
  connect --apn ctnet
```

注意：`--device`、`--interface` 等全局参数必须放在 `connect`、`doctor`、`status` 或 `disconnect` 子命令之前。

## 9. 仅测试而不改变现有出口

可以提高 4G 默认路由 metric：

```bash
sudo dji-qmi-network connect --apn ctnet --metric 1000
```

然后始终通过 `--interface` 或 `ping -I` 指定 4G 接口测试。

## 10. 非正常退出后的清理

若机器断电或脚本被强制结束，可能残留接口地址或路由。先尝试：

```bash
sudo dji-qmi-network disconnect
```

若状态文件已经丢失，可手动检查并清理：

```bash
ip addr show wwp0s20f0u6i4
ip route
sudo ip addr flush dev wwp0s20f0u6i4
sudo resolvectl revert wwp0s20f0u6i4
```

然后重新执行 `doctor` 和 `connect`。