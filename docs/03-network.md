# 一键联网

`dji-qmi-network` 用于完成 QMI 诊断、数据会话建立、Linux 网络配置、状态查看和断开清理。

## 联网流程

```text
USB 识别
   │
   ▼
qmi_wwan
   │
   ▼
/dev/cdc-wdm*
   │
   ▼
SIM Ready
   │
   ▼
LTE Registered
   │
   ▼
PS Attached
   │
   ▼
WDS Start Network
   │
   ▼
读取 IPv4 / Gateway / DNS / MTU
   │
   ▼
配置 Linux 网络接口
   │
   ▼
Internet
```

## 第一步：诊断

```bash
sudo dji-qmi-network doctor
```

诊断会检查：

- `qmicli` 和 `ip` 命令是否存在。
- `/dev/cdc-wdm*` QMI 设备是否存在。
- QMI 设备对应的 WWAN 接口是否存在。
- Raw-IP 控制节点及当前值。
- QMI 控制通道能否通信。
- SIM 是否为 `present` 和 `ready`。
- LTE 是否已注册、PS 数据业务是否已附着。
- ModemManager 是否正在运行并可能占用设备。

一次实机成功输出如下，设备名会随机器和 USB 端口变化：

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

这里的 `/dev/cdc-wdm0` 和 `wwp0s20f0u6i4` 仅为一次实机示例，不是固定名称。

## 第二步：联网

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

物联网卡或专网卡：

```bash
sudo dji-qmi-network connect --apn YOUR_APN
```

| SIM 类型 | 常见 APN |
| --- | --- |
| 中国电信 | `ctnet` |
| 中国移动 | `cmnet` |
| 中国联通 | `3gnet` |
| 物联网卡、专网卡 | 卡商提供的 APN |

具体 APN 以运营商或卡商提供的信息为准。

一次中国电信实机连接曾取得 `10.5.30.188/29`、网关 `10.5.30.189`、DNS `202.96.128.86` 和 `202.96.134.133`，公网出口为 `183.46.67.30`。这些地址只记录当次测试结果，运营商会动态分配，不能用于其他连接的静态配置。

## `connect` 内部流程

工具自动执行：

1. 检测 QMI 设备。
2. 定位对应 WWAN 接口。
3. 检测并停止可能冲突的 ModemManager。
4. 启用 QMI Raw-IP。
5. 检查 SIM 状态。
6. 等待网络注册和 PS 附着。
7. 建立 QMI WDS 会话。
8. 获取 IPv4、掩码、网关、DNS 和 MTU。
9. 配置 Linux 网络接口。
10. 添加带 metric 的默认路由。
11. 在可用时通过 `resolvectl` 配置链路 DNS。
12. 通过指定 WWAN 接口测试连通性，并可选查询公网出口。
13. 保存运行状态。

状态文件位置：

```text
/run/dji-qmi-network.json
```

其中包括设备、接口、APN、网络参数和会话标识：

- CID：QMI WDS 客户端 ID。
- PDH：Packet Data Handle，即本次分组数据会话句柄。

后续 `disconnect` 使用 CID 和 PDH 精确停止本次会话。状态文件位于 `/run`，重启后不会长期保留。

## 路由 metric

默认 metric：

```text
50
```

Linux 通常优先选择 metric 数值更小的路由。若现有有线网络 metric 为 `100`，4G metric `50` 通常会成为默认出口。

让 4G 作为优先级较低的备用网络：

```bash
sudo dji-qmi-network connect --apn ctnet --metric 500
```

实际选路还会受到路由前缀、策略路由和 NetworkManager 配置影响，可使用 `ip route` 核对。

## 指定设备和接口

存在多个 QMI 设备或多个 WWAN 接口时，应显式指定对应关系：

```bash
sudo dji-qmi-network \
  --device /dev/cdc-wdm0 \
  --interface wwp0s20f0u6i4 \
  connect --apn ctnet
```

示例名称必须替换为本机实际值。`--device`、`--interface` 等全局参数要放在 `connect`、`doctor`、`status` 或 `disconnect` 子命令前面。

## 查看状态

```bash
sudo dji-qmi-network status
```

输出用于核对：

- QMI 设备和网络接口。
- ModemManager 当前状态。
- 网络注册状态和数据附着状态。
- 接口当前 IPv4 地址。
- 已保存的 APN。
- 已保存的 CID/PDH。
- `/run/dji-qmi-network.json` 状态文件。

`status` 同时查询实时 QMI 状态并读取已保存会话；没有状态文件时会明确显示当前未保存连接状态。

## 断开

```bash
sudo dji-qmi-network disconnect
```

工具会：

- 使用 CID/PDH 停止 WDS 会话。
- 清理本工具添加的默认路由。
- 清理接口 IPv4 地址。
- 使用 `resolvectl revert` 重置链路 DNS。
- 删除 `/run/dji-qmi-network.json`。
- 恢复连接时由工具自动停止的 ModemManager。

不恢复 ModemManager：

```bash
sudo dji-qmi-network disconnect --no-restore-modemmanager
```

如果连接并非由本工具建立、状态文件已丢失或损坏，`disconnect` 无法获知原 CID/PDH，应按[故障排查](04-troubleshooting.md)中的残留配置步骤处理。

## 手工验证

连接后将占位符替换为 `doctor` 或 `status` 显示的实际接口名：

```bash
ping -I <WWAN接口> -c 4 223.5.5.5
curl --interface <WWAN接口> https://ifconfig.me
```

第一条验证指定接口的 IP 连通性，第二条查询该接口对应的公网出口。接口地址和公网出口都可能随每次连接变化。

