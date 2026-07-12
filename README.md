# DJI 百旺(QDC507) 模块改装工具

## 本次成果
- 成功识别 DJI 百旺 QDC507 模块。
- 确认模块支持 QMI。
- 使用 `AT+QCFG="usbid"` 将 VID/PID 从 `2CA3:4006` 固化为 `2C7C:0125`。
- Linux 可自动加载 `option` 与 `qmi_wwan` 驱动。
- 自动生成 `/dev/cdc-wdm0` 与 `wwp*` 网络接口。
- 每块模块按 IMEI 自动备份配置。

## 为什么使用 usbid
转换时仅修改 VID/PID，不改变 USB 功能布局，风险更低。
恢复时使用完整 `usbcfg`，确保恢复到原始状态。

## 获取源码

项目仓库：[maomomo-eth/dji-4g-dongle.git](https://github.com/maomomo-eth/dji-4g-dongle.git)

克隆仓库：

```bash
git clone https://github.com/maomomo-eth/dji-4g-dongle.git
cd dji-4g-dongle
```

## 依赖安装

工具运行在 Linux 环境，需要系统能识别 USB 串口与 QMI 设备。

Debian / Ubuntu / Raspberry Pi OS 可直接安装：

```bash
sudo apt update
sudo apt install python3 python3-serial libqmi-utils usbutils -y
```

依赖说明：

- `python3`：运行本工具。
- `python3-serial`：提供 Python `serial` 模块，用于访问 AT 串口。
- `libqmi-utils`：提供 `qmicli`，用于读取 QMI 设备状态、SIM 状态、信号等信息。
- `usbutils`：提供 `lsusb`，用于识别模块 VID/PID。

安装后可先检查依赖是否可用：

```bash
python3 -c "import serial; print('python3-serial OK')"
qmicli --version
lsusb
```

如果系统没有 `python3-serial` 包，也可以使用 pip 安装：

```bash
python3 -m pip install pyserial
```

## 安装工具

在仓库目录中执行：

```bash
sudo cp dji-baiwang-tool /usr/local/sbin/
sudo chmod +x /usr/local/sbin/dji-baiwang-tool
```

## 常用命令
查看状态：
```bash
sudo dji-baiwang-tool status
```

备份：
```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups backup
```

转换：
```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups convert --yes
```

恢复：
```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups restore --yes
```

验证：
```bash
sudo dji-baiwang-tool verify --require-standard
```

批量：
```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups batch --yes
```

## 批量模式说明

`batch` 不是单纯批量备份，而是连续处理多块模块：

1. 等待插入一块模块。
2. 自动读取模块 IMEI 和当前 USB 配置。
3. 先按 IMEI 保存原始备份。
4. 如果当前 VID/PID 不是 `2C7C:0125`，自动写入 `AT+QCFG="usbid",11388,293`。
5. 提示拔出当前模块。
6. 插入下一块模块后继续处理。

批量模式适合连续改装多块 DJI 百旺 QDC507 模块。每次仍然只允许连接一块模块，处理完成后按提示拔出，再插入下一块。

如果只想备份当前插入的单块模块，不要使用 `batch`，使用：

```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups backup
```

批量模式常用参数：

- `--yes`：确认进入批量写入模式，必须添加。
- `--restart`：每块写入后执行 `AT+CFUN=1,1` 重启模块。
- `--wait-timeout <秒>`：等待模块插入的超时时间，`0` 表示一直等待。
- `--remove-timeout <秒>`：等待模块拔出的超时时间，默认 `120` 秒。

示例：

```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups batch --yes
```

如果希望写入后自动重启模块：

```bash
sudo dji-baiwang-tool --backup-dir ~/dev/dji/backups batch --yes --restart
```

## 备份格式
文件名：
```
IMEI-固件-时间.json
```
并生成：
```
IMEI-latest.json
```

## 注意事项
- 一次仅连接一块模块。
- 转换后重新拔插模块。
- 恢复会按 IMEI 自动匹配备份。
- 未插 SIM 时出现 `no-atr-received` 属正常现象。
