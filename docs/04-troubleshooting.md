# 故障排查

本文汇总 DJI 百旺 QDC507 在 Linux 上改装和 QMI 联网时最常见的问题。

## 1. 找不到 `/dev/cdc-wdm0`

先检查 USB 和驱动：

```bash
lsusb
lsusb -t
```

正常布局应包含：

```text
Driver=option
Driver=qmi_wwan
```

加载驱动：

```bash
sudo modprobe option
sudo modprobe qmi_wwan
sudo modprobe cdc_wdm
```

重新拔插模块后检查：

```bash
ls -l /dev/cdc-wdm*
ip link
```

若模块仍为原始 `2CA3:4006`，内核可能没有该 VID/PID 的自动匹配规则。建议先使用本项目完成 VID/PID 转换，或根据实际接口谨慎手动绑定驱动。

## 2. `qmicli` 提示权限不足

错误示例：

```text
Cannot open device file '/dev/cdc-wdm0': 权限不够
```

使用 root 权限：

```bash
sudo qmicli -d /dev/cdc-wdm0 --dms-get-model
```

本项目的网络管理命令也应使用 `sudo`。

## 3. `endpoint hangup` 或 CID 分配失败

错误示例：

```text
CID allocation failed in the CTL client: endpoint hangup
```

最常见原因是 `ModemManager` 抢占 QMI 控制通道。

检查：

```bash
systemctl status ModemManager
```

临时停止：

```bash
sudo systemctl stop ModemManager
sudo qmicli -d /dev/cdc-wdm0 --dms-get-model
```

专用机器可禁用：

```bash
sudo systemctl disable --now ModemManager
```

`dji-qmi-network connect` 会自动处理该冲突。

## 4. AT 串口被占用

错误通常表现为：

- 找不到可用 AT 串口
- `Resource busy`
- 所有 `/dev/ttyUSB*` 都不返回 `OK`

检查占用：

```bash
sudo lsof /dev/ttyUSB2
sudo fuser -v /dev/ttyUSB2
```

关闭 `picocom`、其他串口终端或 ModemManager 后重试。

## 5. SIM 未识别

检查：

```bash
sudo qmicli -d /dev/cdc-wdm0 --uim-get-card-status
```

正常应包含：

```text
Card state: 'present'
Application state: 'ready'
```

若出现 `no-atr-received`：

- 检查 SIM 是否插紧。
- 检查卡槽方向。
- 重新断电插拔模块。
- 换一张已知正常的 SIM 测试。

## 6. PIN 未解锁

若 SIM 开启 PIN，模块可能无法驻网。可通过 AT 口检查：

```text
AT+CPIN?
```

返回 `READY` 表示正常。输入 PIN 属高风险操作，连续输错可能锁卡，请使用运营商提供的正确 PIN。

## 7. `registered=False`

检查驻网：

```bash
sudo qmicli -d /dev/cdc-wdm0 --nas-get-serving-system
sudo qmicli -d /dev/cdc-wdm0 --nas-get-signal-strength
```

可能原因：

- 信号太弱。
- SIM 欠费、停机或无数据权限。
- 当前频段或网络制式不支持。
- 天线未接好。
- 运营商网络暂时不可用。

将模块移到信号更好的位置并重新测试。

## 8. 已注册但 `PS: detached`

`registered` 只表示已登记到运营商网络，`PS attached` 才表示数据业务已附着。

可能原因：

- SIM 未开通数据业务。
- APN 不正确。
- 运营商侧拒绝数据附着。
- 模块仍在初始化。

等待几十秒后再次运行：

```bash
sudo dji-qmi-network doctor
```

## 9. 拨号成功但接口没有 IPv4

这是 QMI Raw-IP 环境的常见现象：

```text
Network started successfully
```

只代表 WDS 会话建立，不代表 Linux 已自动配置地址。

查看运营商参数：

```bash
sudo qmicli -d /dev/cdc-wdm0 \
  --device-open-proxy \
  --wds-get-current-settings
```

推荐直接使用：

```bash
sudo dji-qmi-network connect --apn ctnet
```

工具会自动写入 IPv4、路由、MTU 和 DNS。

## 10. `Raw-IP` 不是 `Y`

检查：

```bash
cat /sys/class/net/wwp0s20f0u6i4/qmi/raw_ip
```

切换前先关闭接口：

```bash
sudo ip link set wwp0s20f0u6i4 down
echo Y | sudo tee /sys/class/net/wwp0s20f0u6i4/qmi/raw_ip
sudo ip link set wwp0s20f0u6i4 up
```

`dji-qmi-network connect` 会自动完成这一过程。

## 11. 能 ping IP，不能访问域名

这是 DNS 问题。

检查：

```bash
resolvectl status wwp0s20f0u6i4
```

测试 IP：

```bash
ping -I wwp0s20f0u6i4 -c 4 223.5.5.5
```

测试域名：

```bash
ping -I wwp0s20f0u6i4 -c 4 www.baidu.com
```

手动设置链路 DNS：

```bash
sudo resolvectl dns wwp0s20f0u6i4 202.96.128.86 202.96.134.133
sudo resolvectl domain wwp0s20f0u6i4 '~.'
```

恢复：

```bash
sudo resolvectl revert wwp0s20f0u6i4
```

## 12. 4G 已连接，但默认流量仍走有线

查看：

```bash
ip route
```

Linux 优先选择较小的 metric。连接时可指定：

```bash
sudo dji-qmi-network connect --apn ctnet --metric 50
```

若不想让 4G 抢占默认路由，改用较大值：

```bash
sudo dji-qmi-network connect --apn ctnet --metric 500
```

## 13. 断开后还有残留地址或路由

先运行：

```bash
sudo dji-qmi-network disconnect
```

若状态文件损坏或丢失，手动清理：

```bash
sudo ip addr flush dev wwp0s20f0u6i4
sudo ip route del default dev wwp0s20f0u6i4 2>/dev/null || true
sudo resolvectl revert wwp0s20f0u6i4
```

再检查：

```bash
ip addr show wwp0s20f0u6i4
ip route
```

## 14. `udhcpc: command not found`

Ubuntu 默认通常没有 `udhcpc`。本模块实测由 QMI 返回静态 Raw-IP 参数，并不依赖 DHCP。

无需安装 `udhcpc`，直接使用：

```bash
sudo dji-qmi-network connect --apn ctnet
```

## 15. 多个 QMI 设备导致识别错误

明确指定设备和接口：

```bash
sudo dji-qmi-network \
  --device /dev/cdc-wdm0 \
  --interface wwp0s20f0u6i4 \
  doctor
```

连接：

```bash
sudo dji-qmi-network \
  --device /dev/cdc-wdm0 \
  --interface wwp0s20f0u6i4 \
  connect --apn ctnet
```

## 16. 收集诊断信息

报告问题时建议附上：

```bash
lsusb
lsusb -t
ip link
ip addr
ip route
ls -l /dev/cdc-wdm* /dev/ttyUSB* 2>/dev/null
systemctl status ModemManager --no-pager
sudo dji-qmi-network doctor
sudo qmicli -d /dev/cdc-wdm0 --nas-get-serving-system
sudo qmicli -d /dev/cdc-wdm0 --nas-get-signal-strength
```

请在公开日志中隐藏 IMEI、ICCID、电话号码等敏感信息。