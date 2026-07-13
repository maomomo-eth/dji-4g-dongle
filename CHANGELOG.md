# 变更记录

本项目采用语义化版本思路维护重要变更。

## [未发布]

### 新增

- 新增 `dji-qmi-network`：
  - `doctor`：检查 QMI、SIM、LTE、Raw-IP 和 ModemManager。
  - `connect`：一键拨号并配置 IPv4、路由、DNS、MTU。
  - `status`：查看当前数据连接状态。
  - `disconnect`：释放 WDS 会话并清理网络配置。
- 新增完整文档：
  - 安装与卸载
  - 模块改装
  - 一键联网
  - 故障排查
  - FAQ
- 新增 GitHub Issue 与 PR 模板。

### 已验证

- Ubuntu 24.04
- DJI 百旺 QDC507
- 固件 `QDC507GLEFM21`
- 中国电信 LTE，APN `ctnet`
- QMI Raw-IP

## [0.1.0] - 2026-07-13

### 新增

- `dji-baiwang-tool`
- 按 IMEI 备份原始 USB 配置
- 将 VID/PID 转换为 `2C7C:0125`
- 按 IMEI 恢复原始 `usbcfg` / `usbnet`
- USB、QMI、SIM、注册和信号验证
- 多模块批量处理
