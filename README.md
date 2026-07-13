# DJI 百旺（QDC507）4G 模块改装与联网工具

本项目用于在 Linux 上改装和使用 DJI 百旺 QDC507 4G 模块，包含：

- 按 IMEI 备份模块原始 USB 配置。
- 将 VID/PID 固化为标准 Quectel `2C7C:0125`。
- 恢复模块原始 `usbcfg` / `usbnet` 配置。
- 验证 USB、QMI、SIM、LTE 注册和信号状态。
- 连续处理多块模块。
- 使用 QMI 一键拨号，并自动配置 IPv4、默认路由和 DNS。
- 自动处理 Ubuntu 上 `ModemManager` 抢占 QMI 控制通道的问题。

## 已验证环境

- 模块：DJI 百旺 QDC507
- 固件：`QDC507GLEFM21`
- 原始 USB ID：`2CA3:4006`
- 标准 USB ID：`2C7C:0125`
- USB 网络模式：QMI Raw-IP
- 系统：Ubuntu 24.04
- 运营商：中国电信 LTE，APN `ctnet`

## 为什么只修改 usbid

转换时仅修改 VID/PID，不改变已经验证可用的 USB 功能布局，风险更低。恢复时则使用备份中的完整 `usbcfg` 和 `usbnet`，确保可以还原原始状态。

## 获取源码

```bash
git clone https://github.com/maomomo-eth/dji-4g-dongle.git
cd dji-4g-dongle
```

## 安装依赖

Debian、Ubuntu、Raspberry Pi OS：

```bash
sudo apt update
sudo apt install python3 python3-serial libqmi-utils usbutils iproute2 curl -y
```

依赖说明：

- `python3`：运行两个工具。
- `python3-serial`：访问模块 AT 串口。
- `libqmi-utils`：提供 `qmicli` 和 `qmi-network`。
- `usbutils`：提供 `lsusb`。
- `iproute2`：配置接口地址和路由。
- `curl`：可选，用于显示 4G 公网出口 IP。

## 安装工具

```bash
sudo install -m 0755 dji-baiwang-tool /usr/local/sbin/dji-baiwang-tool
sudo install -m 0755 dji-qmi-network /usr/local/sbin/dji-qmi-network
```

工具分工：

- `dji-baiwang-tool`：配置备份、VID/PID 转换、恢复和硬件验证。
- `dji-qmi-network`：QMI 驻网诊断、拨号、IP/路由/DNS 配置和断开。

# 一键联网

## 1. 先诊断

```bash
sudo dji-qmi-network doctor
```

诊断内容包括：

- `qmicli` 和 `ip` 是否已安装。
- `/dev/cdc-wdm*` 是否存在。
- QMI 对应 WWAN 接口是否存在。
- Raw-IP 状态。
- QMI 控制通道是否可通信。
- SIM 卡是否就绪。
- 是否已注册 LTE 并完成 PS 附着。
- `ModemManager` 是否正在占用设备。

## 2. 连接中国电信

```bash
sudo dji-qmi-network connect
```

默认 APN 为 `ctnet`，默认 4G 路由 metric 为 `50`。连接过程会自动：

1. 检测并停止 `ModemManager`。
2. 检测 `/dev/cdc-wdm*` 和对应 WWAN 接口。
3. 启用 QMI Raw-IP。
4. 检查 SIM 和 LTE 注册状态。
5. 使用 `qmicli` 建立 WDS 数据连接。
6. 读取运营商下发的 IPv4、掩码、网关、DNS 和 MTU。
7. 配置接口地址和默认路由。
8. 使用 `resolvectl` 配置链路 DNS。
9. 通过指定 4G 接口执行 ping，并尝试显示公网出口 IP。

成功后会创建运行状态文件：

```text
/run/dji-qmi-network.json
```

其中保存 WDS CID、Packet Data Handle、接口、地址和路由信息，供断开时精确清理。

## 3. 指定其他 APN

中国移动：

```bash
sudo dji-qmi-network connect --apn cmnet
```

中国联通：

```bash
sudo dji-qmi-network connect --apn 3gnet
```

物联网卡请使用卡商提供的 APN：

```bash
sudo dji-qmi-network connect --apn YOUR_APN
```

## 4. 不抢占现有默认路由

默认 metric 为 `50`，通常会优先于有线或 Wi-Fi。若只想保留 4G 备用路由，可提高 metric：

```bash
sudo dji-qmi-network connect --metric 500
```

也可以只通过指定接口测试：

```bash
ping -I wwp0s20f0u6i4 223.5.5.5
curl --interface wwp0s20f0u6i4 https://ifconfig.me
```

## 5. 查看状态

```bash
sudo dji-qmi-network status
```

## 6. 断开并恢复网络

```bash
sudo dji-qmi-network disconnect
```

该命令会：

- 使用保存的 CID 和 Packet Data Handle 停止 WDS 会话。
- 删除该接口的默认路由和 IPv4 地址。
- 恢复 `resolvectl` 链路 DNS。
- 删除运行状态文件。
- 若连接时自动停止了 `ModemManager`，默认重新启动它。

若不希望恢复 `ModemManager`：

```bash
sudo dji-qmi-network disconnect --no-restore-modemmanager
```

# 模块改装工具

## 查看模块状态

```bash
sudo dji-baiwang-tool status
```

## 备份

```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups backup
```

## 转换 VID/PID

```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups convert --yes
```

写入后自动重启模块：

```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups convert --yes --restart
```

## 恢复原始配置

```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups restore --yes
```

## 验证

```bash
sudo dji-baiwang-tool verify --require-standard
```

显示完整 QMI 返回：

```bash
sudo dji-baiwang-tool verify --require-standard --verbose
```

## 批量模式

```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups batch --yes
```

批量模式会连续处理多块模块：

1. 等待插入一块模块。
2. 自动读取 IMEI 和当前 USB 配置。
3. 按 IMEI 保存原始备份。
4. 如果当前不是 `2C7C:0125`，写入标准 VID/PID。
5. 提示拔出当前模块。
6. 插入下一块后继续。

一次仍然只允许连接一块模块。

# ModemManager 冲突

Ubuntu 默认的 `ModemManager` 可能抢占 `/dev/cdc-wdm0`，常见错误为：

```text
CID allocation failed in the CTL client: endpoint hangup
```

`dji-qmi-network connect` 会在联网前自动停止它，并在正常断开时恢复。手动排查可以执行：

```bash
sudo systemctl stop ModemManager
sudo qmicli -d /dev/cdc-wdm0 --dms-get-model
```

若机器专门使用本模块，也可以禁用：

```bash
sudo systemctl disable --now ModemManager
```

# 常见问题

## qmi-network 显示 Network started，但接口没有 IPv4

这是正常现象。`qmi-network` 主要负责建立 WDS 数据会话，不一定会把运营商返回的静态 Raw-IP 参数写入 Linux 接口。

本项目的 `dji-qmi-network connect` 会调用 `--wds-get-current-settings`，然后自动配置 IP、网关、DNS 和 MTU，不依赖 `udhcpc`。

## `udhcpc: command not found`

Ubuntu 默认通常没有 `udhcpc`。对于本模块已验证的 QMI Raw-IP 工作方式，不需要安装它。

## 发现多个 `/dev/cdc-wdm*` 或 WWAN 接口

请手动指定：

```bash
sudo dji-qmi-network \
  --device /dev/cdc-wdm0 \
  --interface wwp0s20f0u6i4 \
  connect --apn ctnet
```

注意：全局参数必须放在子命令 `connect` 前面。

# 备份格式

备份文件名：

```text
IMEI-固件-时间.json
```

同时生成：

```text
IMEI-latest.json
```

# 注意事项

- 一次仅连接一块模块。
- 修改 VID/PID 前务必保存备份。
- 转换后需要重新拔插模块，或使用 `--restart`。
- 恢复会按 IMEI 自动匹配备份。
- 未插 SIM 时出现 `no-atr-received` 属正常现象。
- `connect` 会新增一条默认路由；通过 `--metric` 控制其优先级。
- 非正常关机可能残留接口配置；可手动执行 `ip addr flush dev <接口>` 后重试。
