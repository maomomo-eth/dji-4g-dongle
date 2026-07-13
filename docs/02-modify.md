# 模块改装

本文介绍如何识别、备份、转换和恢复 DJI 百旺 QDC507 4G 模块。

## 1. 改装目标

原始模块使用 DJI/百旺 USB ID：

```text
2CA3:4006
```

本项目将其 VID/PID 持久化改为标准 Quectel：

```text
2C7C:0125
```

转换时只修改 `usbid`，不改动已经验证可用的 USB 功能布局。模块继续提供：

- `option` 串口驱动
- `qmi_wwan` 网络驱动
- `/dev/cdc-wdm0` QMI 控制设备
- `wwp*` / `wwan*` 网络接口

## 2. 改装前准备

一次只连接一块模块，并确保已经安装工具：

```bash
sudo dji-baiwang-tool status
```

典型输出：

```text
AT 端口：/dev/ttyUSB2
IMEI：863212060502298
固件：QDC507GLEFM21
USBID：2CA3:4006
USBCFG：2CA3:4006, diag=1, nmea=1, at=1, modem=1, rmnet=1, adb=0, uac=0
USBNET：0
```

字段说明：

- `AT 端口`：可响应 AT 命令的串口。
- `IMEI`：用于为每块模块匹配独立备份。
- `固件`：当前模块固件版本。
- `USBID`：当前持久化 VID/PID。
- `USBCFG`：USB 功能布局。
- `USBNET`：USB 网络模式，本项目实测为 QMI Raw-IP。

## 3. 先备份原始配置

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  backup
```

备份文件示例：

```text
863212060502298-QDC507GLEFM21-20260713-143000.json
863212060502298-latest.json
```

备份包含：

- IMEI
- 固件版本
- `usbcfg`
- `usbnet`
- `usbid`
- 原始 AT 返回

不要跳过备份。恢复操作会按当前模块 IMEI 自动寻找对应备份。

## 4. 转换 VID/PID

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  convert --yes
```

工具会先再次备份，然后执行：

```text
AT+QCFG="usbid",11388,293
```

十进制 `11388:293` 即十六进制 `2C7C:0125`。

转换完成后，断电重新拔插模块。也可以让工具自动重启：

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  convert --yes --restart
```

执行 `--restart` 后串口断开和 USB 重新枚举属于正常现象。

## 5. 验证改装结果

先查看 USB ID：

```bash
lsusb
```

应能看到：

```text
ID 2c7c:0125 Quectel Wireless Solutions Co., Ltd.
```

检查驱动布局：

```bash
lsusb -t
```

目标布局应包含至少四个 `option` 接口和一个 `qmi_wwan` 接口，例如：

```text
If 0, Driver=option
If 1, Driver=option
If 2, Driver=option
If 3, Driver=option
If 4, Driver=qmi_wwan
```

运行完整验证：

```bash
sudo dji-baiwang-tool verify --require-standard
```

需要查看完整 QMI 返回时：

```bash
sudo dji-baiwang-tool verify --require-standard --verbose
```

## 6. 驱动和设备含义

### option

负责模块的多个 USB 串口，常见用途包括诊断、NMEA、AT 命令和 Modem 端口。

### qmi_wwan

负责 QMI 数据网络接口，成功绑定后会创建 `wwp*`、`wwan*` 或 `wwx*` 接口。

### cdc_wdm

提供 QMI 控制设备，通常为：

```text
/dev/cdc-wdm0
```

`qmicli` 通过该设备查询 SIM、信号、驻网状态并建立 WDS 数据连接。

## 7. 恢复原始配置

按当前 IMEI 自动寻找最新备份：

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  restore --yes
```

指定备份文件：

```bash
sudo dji-baiwang-tool \
  restore --file ~/dev/dji/backups/IMEI-latest.json --yes
```

恢复时会先写入备份中的 `usbnet`，再写入完整 `usbcfg`。完成后需要重新拔插，或者添加：

```bash
--restart
```

默认拒绝把其他 IMEI 的备份写入当前模块。确需跨模块恢复时可使用 `--force`，但风险较高。

## 8. 批量改装

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  batch --yes
```

流程为：

1. 等待插入一块模块。
2. 自动读取 IMEI 和配置。
3. 按 IMEI 保存备份。
4. 写入 `2C7C:0125`。
5. 提示拔出模块。
6. 插入下一块继续。

批量模式仍要求一次只连接一块模块。

## 9. 风险提示

- 修改前必须保存原始备份。
- 写入过程中不要断电或拔出模块。
- 不要随意修改未知的 `usbcfg` 功能位。
- 本项目不刷写基带固件，只修改模块配置。
- 未插 SIM 时出现 `no-atr-received` 通常属于正常现象。