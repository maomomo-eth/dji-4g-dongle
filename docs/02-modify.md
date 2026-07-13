# 模块改装

本文说明如何使用 `dji-baiwang-tool` 备份、转换、验证和恢复 DJI 百旺 QDC507。

## 改装目标

将模块 USB ID 从：

```text
2CA3:4006
```

修改为标准 Quectel：

```text
2C7C:0125
```

`convert` 只修改 `usbid`，不改变已经验证可用的 USB 功能布局。工具仍会把完整 `usbcfg`、`usbnet` 和 `usbid` 写入备份，但只有执行恢复时才会写回完整 `usbnet` 和 `usbcfg`。

改装时一次只连接一块模块，写入过程中不要断电。

## 第一步：连接并查看状态

```bash
sudo dji-baiwang-tool status
```

常见字段：

- `AT 端口`：自动扫描后找到的可响应 AT 命令的串口。
- `IMEI`：模块唯一标识，用于匹配独立备份。
- `固件`：模块当前固件版本。
- `USBID`：当前持久化 VID/PID。
- `USBCFG`：USB 串口和网络等功能布局。
- `USBNET`：USB 网络模式配置。

不同机器上的 AT 端口编号可能不同，不要预先写死为某个 `/dev/ttyUSB*`。

## 第二步：备份

推荐将备份放在仓库之外的持久目录：

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  backup
```

文件命名格式：

```text
IMEI-固件-时间.json
IMEI-latest.json
```

`IMEI-latest.json` 指向或复制该 IMEI 的最新备份。备份包括完整 `usbcfg`、`usbnet`、`usbid` 和原始 AT 返回，应妥善保留。

注意：在 `sudo` 环境中，`~` 的展开行为取决于 shell。若希望路径毫无歧义，可改用当前用户目录的绝对路径，例如 `$HOME/dev/dji/backups` 展开后的实际路径。

## 第三步：转换 VID/PID

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  convert --yes
```

`convert` 会再次自动备份，然后仅写入 `usbid`。不加 `--restart` 时，完成后需要断电重新拔插模块，让 USB 重新枚举。

可选自动重启模块：

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  convert --yes --restart
```

使用 `--restart` 后串口断开属于正常现象，等待设备重新枚举即可。

## 第四步：验证

```bash
lsusb
lsusb -t
sudo dji-baiwang-tool verify --require-standard
```

期望看到：

- USB ID 为 `2C7C:0125`。
- `option` 至少绑定 4 个接口。
- `qmi_wwan` 至少绑定 1 个接口。
- 出现 `/dev/cdc-wdm*` QMI 控制设备。
- 出现 `wwp*`、`wwan*` 或 `wwx*` 网络接口。

实际设备编号和网络接口名由内核及 USB 拓扑决定，不要写死。需要完整 QMI 返回时使用：

```bash
sudo dji-baiwang-tool verify --require-standard --verbose
```

## 恢复

默认按当前模块 IMEI 查找最新备份：

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  restore --yes
```

也可以指定备份文件：

```bash
sudo dji-baiwang-tool \
  restore \
  --file /path/to/backup.json \
  --yes
```

恢复会先写回备份中的 `usbnet`，最后写回完整 `usbcfg`，因为后者可能触发 USB 重新枚举。

- 默认按当前 IMEI 匹配备份。
- 指定文件时仍会校验备份 IMEI。
- 跨 IMEI 恢复必须添加 `--force`。
- `--force` 可能把不兼容的完整 USB 配置写入另一块模块，不推荐普通用户使用。

恢复后按提示重新拔插，或在命令末尾添加 `--restart`。

## 批量模式

```bash
sudo dji-baiwang-tool \
  --backup-dir ~/dev/dji/backups \
  batch --yes
```

批量模式仍然是逐块处理：

1. 一次只连接一块模块。
2. 工具读取 IMEI 和当前配置并单独备份。
3. 工具按需写入 `2C7C:0125`。
4. 处理完成后拔出当前模块，再插入下一块。

每块模块都按 IMEI 建立独立备份，不要交换备份文件。

## 安全限制

- 修改前必须备份，并确认备份文件可以读取。
- 不要使用其他模块的完整 `usbcfg` 完成 VID/PID 修改。
- 写入和重新枚举期间不要断电或拔出设备。
- 本工具不刷写基带固件，但持久化 USB 配置仍有风险。
- 当前仅实机验证 `QDC507GLEFM21`；其他固件和批次可能需要额外适配。

