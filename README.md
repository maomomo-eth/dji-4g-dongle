# DJI 4G Dongle Toolkit

一个用于 Linux 的 DJI 百旺 QDC507 模块改装、备份、恢复、QMI 联网和故障诊断工具。

## 已验证环境

- 模块：DJI 百旺 QDC507
- 固件：`QDC507GLEFM21`
- 原始 USB ID：`2CA3:4006`
- 修改后 USB ID：`2C7C:0125`
- USB 网络模式：QMI Raw-IP
- 系统：Ubuntu 24.04
- 运营商：中国电信，APN `ctnet`

其他固件、模块批次、运营商和发行版可能需要额外适配。

## 功能概览

### `dji-baiwang-tool`

- 自动扫描 AT 串口并查询模块信息。
- 按 IMEI 备份原始 `usbcfg`、`usbnet` 和 `usbid`。
- 仅将 VID/PID 修改为标准 Quectel `2C7C:0125`。
- 按备份恢复原始 USB 配置。
- 验证 USB、QMI、SIM、网络注册和信号。
- 逐块批量处理多个模块。

### `dji-qmi-network`

- 诊断 QMI 设备、Raw-IP、SIM、注册状态和 ModemManager 冲突。
- 建立 QMI WDS 会话并读取运营商下发的网络参数。
- 自动配置 IPv4、默认路由、MTU 和 DNS。
- 显示连接状态，并使用 CID/PDH 精确断开会话。

## 快速开始

```bash
git clone https://github.com/maomomo-eth/dji-4g-dongle.git
cd dji-4g-dongle

sudo apt update
sudo apt install python3 python3-serial libqmi-utils usbutils iproute2 curl -y

sudo install -m 0755 dji-baiwang-tool /usr/local/sbin/dji-baiwang-tool
sudo install -m 0755 dji-qmi-network /usr/local/sbin/dji-qmi-network

sudo dji-qmi-network doctor
sudo dji-qmi-network connect --apn ctnet
```

修改模块 USB ID 前，请先阅读[模块改装](docs/02-modify.md)并完成备份。

## 文档导航

- [安装与卸载](docs/01-install.md)
- [模块改装](docs/02-modify.md)
- [一键联网](docs/03-network.md)
- [故障排查](docs/04-troubleshooting.md)
- [常见问题](docs/05-faq.md)
- [变更记录](CHANGELOG.md)

## 命令速查

| 命令 | 用途 |
| --- | --- |
| `dji-baiwang-tool status` | 查询 AT 端口、IMEI、固件和 USB 配置 |
| `dji-baiwang-tool backup` | 按 IMEI 备份原始配置 |
| `dji-baiwang-tool convert` | 备份后将 VID/PID 改为 `2C7C:0125` |
| `dji-baiwang-tool restore` | 恢复备份中的完整 USB 配置 |
| `dji-baiwang-tool verify` | 验证 USB、驱动、QMI、SIM 和网络状态 |
| `dji-baiwang-tool batch` | 逐块备份并转换多个模块 |
| `dji-qmi-network doctor` | 检查 QMI 联网前置条件 |
| `dji-qmi-network connect` | 建立数据会话并配置 Linux 网络 |
| `dji-qmi-network status` | 查看实时网络状态和已保存会话 |
| `dji-qmi-network disconnect` | 断开会话并清理网络配置 |

需要写入模块或修改网络的命令应使用 `sudo`。

`connect --force` 不会忽略或覆盖旧状态：工具会先使用旧 CID/PDH 停止会话并清理 IP、路由和 DNS，再建立新连接。状态文件损坏时会拒绝继续。

## 架构图

```text
DJI QDC507
    │ USB
    ▼
option + qmi_wwan
    │
    ├── /dev/ttyUSB*
    ├── /dev/cdc-wdm*
    └── wwp*/wwan*/wwx*
              │
              ▼
          QMI WDS 会话
              │
              ▼
      IPv4 / Route / DNS
              │
              ▼
           Internet
```

## 安全提醒

- 修改 VID/PID 前必须备份原始配置。
- 改装和批量处理时一次只连接一块模块。
- 写入配置过程中不要断电或拔出模块。
- 恢复时必须使用正确 IMEI 对应的备份；`--force` 跨 IMEI 恢复风险较高。
- 本项目不保证适配所有 QDC507 固件、模块批次和运营商环境。
