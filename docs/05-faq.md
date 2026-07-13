# 常见问题

## 支持哪些模块？

目前实机验证的是 DJI 百旺 QDC507，固件 `QDC507GLEFM21`。其他采用 Quectel QMI 接口、USB 功能布局相近的模块可能可用，但修改配置前必须自行备份和验证。

## 支持哪些系统？

已验证 Ubuntu 24.04。Debian、Raspberry Pi OS 等 Debian 系发行版通常也可使用，前提是内核包含 `option`、`qmi_wwan` 和 `cdc_wdm`。

## 支持 Windows 吗？

当前两个工具面向 Linux，依赖 Linux 驱动、`qmicli`、`iproute2` 和 `resolvectl`，不支持 Windows。

## 支持 OpenWrt 吗？

思路相同，但 OpenWrt 的网络管理、DNS、服务脚本与 Ubuntu 不同。当前 `dji-qmi-network` 不应直接用于 OpenWrt，后续可单独适配 `uqmi`、netifd 和 UCI。

## 为什么要修改 VID/PID？

原始 `2CA3:4006` 不一定被通用 Linux 驱动自动识别。改为标准 Quectel `2C7C:0125` 后，常见内核可自动匹配 `option` 和 `qmi_wwan`。

## 修改 VID/PID 会刷固件吗？

不会。本项目只写入模块配置中的 USB ID，不刷写基带固件，也不主动改变已验证可用的 USB 功能布局。

## 为什么必须先备份？

不同批次模块的 `usbcfg`、`usbnet` 或固件可能不同。备份可以按 IMEI 恢复原始配置，避免使用别人的配置覆盖自己的模块。

## 为什么一次只能连接一块模块？

改装工具会自动扫描 AT 串口和目标 USB ID。多块相同模块同时连接时，端口与 IMEI 的对应关系容易混淆，存在改错设备的风险。

## 为什么 `qmi-network` 已成功，但没有 IPv4？

`qmi-network` 主要建立 WDS 数据会话，不一定自动把 QMI 返回的 Raw-IP 参数配置到 Linux 接口。`dji-qmi-network connect` 会继续读取当前设置并配置 IP、路由、MTU 和 DNS。

## 是否需要 `udhcpc`？

不需要。QDC507 的实测链路使用 QMI Raw-IP，地址参数由 WDS 当前设置返回，不依赖 DHCP。

## 为什么要停止 ModemManager？

ModemManager 可能先创建 QMI 客户端并抢占控制通道，导致手动运行 `qmicli` 时出现 CID 分配失败或 `endpoint hangup`。联网工具会按需自动停止，并在断开时恢复。

## 常见 APN 是什么？

| 运营商 | 常见 APN |
| --- | --- |
| 中国移动 | `cmnet` |
| 中国联通 | `3gnet` |
| 中国电信 | `ctnet` |

物联网卡、专网卡和境外 SIM 必须使用运营商或卡商提供的 APN。

## 4G 得到的 `10.x.x.x` 是公网 IP 吗？

通常不是。它是运营商分配给模块的承载网地址，公网访问会经过运营商 NAT。使用 `curl --interface <接口> https://ifconfig.me` 看到的是公网出口 IP。

## 公网出口 IP 为什么会变化？

移动网络通常使用动态地址和运营商级 NAT，重新拨号、切换基站或网络侧调整都可能改变出口 IP。

## 可以同时保留有线和 4G 吗？

可以。通过路由 metric 控制优先级。较小值优先，例如 4G `50`、有线 `100` 时通常优先走 4G；把 4G 设置为 `500` 可作为备用路由。

## 如何只测试 4G，不改变默认出口？

连接时使用较大的 metric，并通过接口明确发起请求：

```bash
sudo dji-qmi-network connect --apn ctnet --metric 1000
ping -I wwp0s20f0u6i4 223.5.5.5
curl --interface wwp0s20f0u6i4 https://ifconfig.me
```

## CID 和 PDH 是什么？

CID 是 QMI WDS 服务客户端 ID，PDH 是本次数据连接的 Packet Data Handle。断开时需要它们准确停止对应会话。

## 状态文件有什么用？

`/run/dji-qmi-network.json` 保存本次连接的设备、接口、CID、PDH、地址、网关、DNS 和 ModemManager 状态，供 `status` 展示和 `disconnect` 精确清理。

## 重启后还需要手动连接吗？

当前版本不会自动开机拨号。可在确认脚本稳定后自行配置 systemd 服务；正式加入项目前还需要设计重试、断线重拨和有线网络回退策略。

## 可以用模块做路由器吗？

可以，但本项目目前只负责主机自身联网。要给其他设备共享网络，还需配置 IPv4 转发、NAT、防火墙和 DHCP/DNS 服务。

## 如何安全提交问题？

提供系统版本、模块固件、`lsusb -t`、`doctor` 和相关错误输出即可。请隐藏 IMEI、ICCID、手机号、账户信息和私有 APN 凭据。