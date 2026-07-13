# 安装与卸载

## 系统要求

已完成实机验证：

- Ubuntu 24.04

以下系统可尝试使用，但当前未完整验证：

- Ubuntu 22.04
- Debian 12
- Raspberry Pi OS

工具依赖 Linux 的 `option`、`qmi_wwan`、`cdc_wdm` 驱动和 systemd-resolved 相关命令。其他发行版可能需要调整软件包名称或 DNS 管理方式。

## 安装依赖

```bash
sudo apt update
sudo apt install \
  python3 \
  python3-serial \
  libqmi-utils \
  usbutils \
  iproute2 \
  curl \
  -y
```

| 软件包 | 作用 |
| --- | --- |
| `python3` | 运行两个 Python 工具 |
| `python3-serial` | 扫描和访问模块 AT 串口 |
| `libqmi-utils` | 提供 `qmicli` 等 QMI 管理命令 |
| `usbutils` | 提供 `lsusb`，检查 USB ID 和驱动布局 |
| `iproute2` | 提供 `ip`，配置接口地址和路由 |
| `curl` | 可选显示指定接口的公网出口地址 |

可选安装 `picocom` 进行手工 AT 调试：

```bash
sudo apt install picocom -y
```

`picocom` 不是一键联网的必需依赖，使用后应退出串口，避免占用 AT 端口。

## 安装工具

在仓库根目录执行：

```bash
sudo install -m 0755 dji-baiwang-tool /usr/local/sbin/dji-baiwang-tool
sudo install -m 0755 dji-qmi-network /usr/local/sbin/dji-qmi-network
```

## 验证安装

```bash
dji-baiwang-tool --help
dji-qmi-network --help
```

若 shell 提示找不到命令，请确认 `/usr/local/sbin` 位于当前用户的 `PATH` 中，或使用完整路径执行。

## 升级

在本地仓库中更新代码并重新安装：

```bash
git pull --ff-only

sudo install -m 0755 dji-baiwang-tool /usr/local/sbin/dji-baiwang-tool
sudo install -m 0755 dji-qmi-network /usr/local/sbin/dji-qmi-network
```

## 卸载

先正常断开当前 QMI 会话：

```bash
sudo dji-qmi-network disconnect
```

删除已安装工具：

```bash
sudo rm -f /usr/local/sbin/dji-baiwang-tool
sudo rm -f /usr/local/sbin/dji-qmi-network
```

清理可能残留的运行状态：

```bash
sudo rm -f /run/dji-qmi-network.json
```

`dji-baiwang-tool` 的默认备份目录是：

```text
/var/lib/dji-baiwang-tool/backups
```

卸载工具时不要默认删除这些备份。确认不再需要恢复任何模块后，才手动删除：

```bash
sudo rm -rf /var/lib/dji-baiwang-tool
```

此命令会永久删除全部模块备份，执行前应另行保存需要保留的 JSON 文件。

## 恢复 ModemManager

若排障时曾手动禁用 ModemManager，可重新启用并立即启动：

```bash
sudo systemctl enable --now ModemManager
```

