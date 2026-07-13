# 安装与卸载

本文介绍在 Debian、Ubuntu、Raspberry Pi OS 等 Linux 系统上安装、升级和卸载本项目。

## 1. 系统要求

已实机验证：

- Ubuntu 24.04
- DJI 百旺 QDC507
- QMI Raw-IP
- 中国电信 LTE，APN `ctnet`

理论上可用于带有 `option`、`qmi_wwan`、`cdc_wdm` 驱动的 Debian 系发行版。

## 2. 安装依赖

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-serial \
  libqmi-utils \
  usbutils \
  iproute2 \
  curl
```

依赖用途：

- `python3`：运行两个工具。
- `python3-serial`：通过 AT 串口读取和修改模块配置。
- `libqmi-utils`：提供 `qmicli` 和 `qmi-network`。
- `usbutils`：提供 `lsusb`。
- `iproute2`：配置接口、地址和路由。
- `curl`：可选，用于查询 4G 公网出口 IP。

若系统未提供 `python3-serial`，可改用：

```bash
python3 -m pip install pyserial
```

## 3. 获取源码

```bash
git clone https://github.com/maomomo-eth/dji-4g-dongle.git
cd dji-4g-dongle
```

## 4. 安装工具

```bash
sudo install -m 0755 dji-baiwang-tool /usr/local/sbin/dji-baiwang-tool
sudo install -m 0755 dji-qmi-network /usr/local/sbin/dji-qmi-network
```

确认安装：

```bash
dji-baiwang-tool --help
dji-qmi-network --help
```

两个工具的分工：

- `dji-baiwang-tool`：备份、VID/PID 转换、恢复、批量改装和硬件验证。
- `dji-qmi-network`：QMI 诊断、联网、状态查看和断开。

## 5. 升级

```bash
cd dji-4g-dongle
git pull
sudo install -m 0755 dji-baiwang-tool /usr/local/sbin/dji-baiwang-tool
sudo install -m 0755 dji-qmi-network /usr/local/sbin/dji-qmi-network
```

升级不会删除 `/var/lib/dji-baiwang-tool/backups` 中的备份。

## 6. 卸载

先断开 QMI 数据连接：

```bash
sudo dji-qmi-network disconnect
```

删除工具：

```bash
sudo rm -f /usr/local/sbin/dji-baiwang-tool
sudo rm -f /usr/local/sbin/dji-qmi-network
```

可选：删除运行状态和备份：

```bash
sudo rm -f /run/dji-qmi-network.json
sudo rm -rf /var/lib/dji-baiwang-tool
```

删除备份前请确认不再需要恢复模块原始配置。

## 7. 恢复 ModemManager

`dji-qmi-network connect` 可能临时停止 `ModemManager`，正常执行 `disconnect` 时会自动恢复。

若此前手动禁用了它，可执行：

```bash
sudo systemctl enable --now ModemManager
```

检查状态：

```bash
systemctl status ModemManager
```

## 8. 权限说明

涉及 USB 串口、QMI 控制设备、IP 地址、路由和 DNS 的操作均需要 root 权限，因此示例命令使用 `sudo`。
