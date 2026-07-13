# 故障排查

以下命令中的 `<接口>`、`<QMI设备>` 必须替换为本机实际名称。公开日志前请隐藏 IMEI、ICCID、手机号和私有 APN 凭据。

## 1. `/dev/cdc-wdm0` 不存在

检查 USB 识别、驱动绑定和内核日志：

```bash
lsusb
lsusb -t
dmesg | grep -Ei 'qmi|wwan|cdc|usb'
```

正常布局应看到：

```text
Driver=qmi_wwan
```

可能原因：

- VID/PID 仍为原始值，内核没有自动匹配。
- `qmi_wwan` 或 `cdc_wdm` 未绑定。
- USB 网络功能布局异常。
- 修改配置后模块尚未重新拔插或重新枚举。

设备也可能命名为 `/dev/cdc-wdm1` 等，不要只检查编号 0。

确认内核提供相应模块后，可手工加载驱动并重新拔插：

```bash
sudo modprobe option
sudo modprobe qmi_wwan
sudo modprobe cdc_wdm
```

若模块仍为原始 `2CA3:4006`，内核可能没有自动匹配该 ID。应优先按[模块改装](02-modify.md)完成备份和转换；手工绑定驱动前必须确认 USB 接口布局。

## 2. `endpoint hangup`

典型错误：

```text
CID allocation failed in the CTL client: endpoint hangup
```

优先排查 ModemManager 冲突：

```bash
sudo systemctl stop ModemManager
sudo qmicli -d /dev/cdc-wdm0 --dms-get-model
```

若停止后恢复正常，说明控制通道曾被占用。`dji-qmi-network connect` 会自动处理，并在正常断开时按需恢复 ModemManager。

## 3. 权限不足

错误示例：

```text
Cannot open device file: 权限不够
```

QMI 控制和网络配置需要 root 权限：

```bash
sudo qmicli -d /dev/cdc-wdm0 --dms-get-model
```

两个项目工具中涉及设备写入、验证和联网的命令也应使用 `sudo`。

## 4. SIM 未识别

```bash
sudo qmicli -d /dev/cdc-wdm0 --uim-get-card-status
```

正常结果应同时包含：

```text
Card state: 'present'
Application state: 'ready'
```

否则检查 SIM 安装方向、卡槽接触、SIM PIN 和模块供电。可换一张已知正常的 SIM 交叉验证。

如果 SIM 启用了 PIN，可通过 AT 端口检查：

```text
AT+CPIN?
```

返回 `READY` 表示已就绪。连续输入错误 PIN 可能锁卡，解锁时只能使用运营商提供的正确 PIN。

## 5. 未注册网络

```bash
sudo qmicli -d /dev/cdc-wdm0 --nas-get-serving-system
```

正常数据连接前应看到：

```text
Registration state: 'registered'
PS: 'attached'
```

可能原因：

- 信号弱或天线连接异常。
- SIM 欠费、停机或未开通数据业务。
- APN 或套餐有接入限制。
- 模块频段与当地网络不兼容。
- 运营商网络暂时不可用。

APN 主要影响数据会话；如果尚未注册，应先检查 SIM、信号、频段和天线。

查询当前信号：

```bash
sudo qmicli -d /dev/cdc-wdm0 --nas-get-signal-strength
```

## 6. `qmi-network` 显示成功但没有 IPv4

`qmi-network` 只负责建立数据会话，不一定配置 Linux 接口。QMI Raw-IP 场景还需要读取 WDS 当前设置并配置地址、路由和 DNS。

推荐直接使用：

```bash
sudo dji-qmi-network connect --apn ctnet
```

APN 应替换为运营商或卡商提供的值。

## 7. `udhcpc: command not found`

Ubuntu 默认没有 `udhcpc`，且本项目已验证流程不依赖它。工具直接读取 QMI WDS 返回的 IPv4、网关、DNS 和 MTU，无需为此安装 DHCP 客户端。

## 8. DNS 不生效

检查指定链路的 DNS：

```bash
resolvectl status <接口>
```

先测试 IP 连通性：

```bash
ping -I <接口> 223.5.5.5
```

再测试域名解析：

```bash
ping -I <接口> www.baidu.com
```

若 IP 可达而域名不可达，检查系统是否使用 systemd-resolved、运营商是否返回 DNS，以及 `resolvectl status <接口>` 是否显示对应链路 DNS。工具仅在 `resolvectl` 可用时自动配置 DNS，其他 DNS 管理方案当前需要额外适配。

## 9. 默认路由不符合预期

```bash
ip route
```

同一目标前缀下通常优先选择 metric 较小的路由。默认 4G metric 为 `50`，作为备用网络可提高到 `500`：

```bash
sudo dji-qmi-network connect --apn ctnet --metric 500
```

策略路由、VPN 或 NetworkManager 可能进一步影响选路，应结合 `ip rule` 和连接配置检查。

## 10. 非正常退出后残留配置

优先使用状态文件正常清理：

```bash
sudo dji-qmi-network disconnect
```

若状态文件丢失，确认接口名后手工清理：

```bash
sudo ip addr flush dev <接口>
sudo ip route del default dev <接口>
sudo resolvectl revert <接口>
```

命令失败时可忽略“对象不存在”类错误。手工清理无法凭空恢复丢失的 CID/PDH；必要时重新枚举模块，以结束无法定位的数据会话。

## 11. 多块模块或多个 QMI 设备

自动检测遇到多个候选设备会拒绝猜测。先根据 USB 拓扑确认设备与接口对应关系，再显式指定：

```bash
sudo dji-qmi-network \
  --device /dev/cdc-wdm0 \
  --interface wwp0s20f0u6i4 \
  doctor

sudo dji-qmi-network \
  --device /dev/cdc-wdm0 \
  --interface wwp0s20f0u6i4 \
  connect --apn ctnet
```

全局参数必须放在子命令前，示例设备名和接口名需替换为本机实际值。模块改装仍要求一次只连接一块。

## 12. AT 串口被占用

若 `dji-baiwang-tool` 找不到可响应的 AT 端口，可检查串口占用：

```bash
sudo lsof /dev/ttyUSB2
sudo fuser -v /dev/ttyUSB2
```

实际 AT 端口不一定是 `ttyUSB2`。退出 `picocom`、串口调试工具或停止占用串口的服务后重试。

## 13. 收集问题信息

提交 Bug 前建议收集：

```bash
uname -a
lsusb
lsusb -t
ip link
ip addr
ip route
systemctl is-active ModemManager
sudo dji-baiwang-tool status
sudo dji-qmi-network doctor
```

同时附上模块固件、SIM 运营商、APN、完整错误输出和做过的额外配置修改。

## 14. Raw-IP 不是 `Y`

先查看实际接口的控制节点：

```bash
cat /sys/class/net/<接口>/qmi/raw_ip
```

`dji-qmi-network connect` 会自动关闭接口、写入 `Y` 并重新启用接口。仅在排查工具失败原因时手工操作：

```bash
sudo ip link set <接口> down
echo Y | sudo tee /sys/class/net/<接口>/qmi/raw_ip
sudo ip link set <接口> up
```

如果控制节点不存在，该接口可能不是 `qmi_wwan` 接口，应回到第 1 节检查驱动绑定。
