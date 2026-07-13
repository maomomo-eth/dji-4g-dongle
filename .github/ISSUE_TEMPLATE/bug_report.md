---
name: Bug 报告
about: 报告模块改装、恢复、诊断或 QMI 联网问题
title: "[Bug] "
labels: bug
assignees: ""
---

## 问题描述

请清晰说明实际行为、期望行为和问题发生的步骤。

## 环境信息

- 系统版本：
- 内核版本（`uname -a`）：
- 模块型号：
- 模块固件：
- SIM 运营商：
- APN：
- ModemManager 是否正在运行：

## 诊断输出

请提供以下命令的完整输出，并隐藏 IMEI、ICCID、手机号和私有凭据。

```text
lsusb
```

```text
lsusb -t
```

```text
sudo dji-qmi-network doctor
```

```text
sudo dji-baiwang-tool status
```

## 完整错误输出

```text
在此粘贴未经截断的错误输出
```

## 额外修改

是否修改过 `usbcfg`、`usbnet`、驱动绑定、NetworkManager、ModemManager、路由、DNS 或脚本？请列出具体操作；若没有，请填写“无”。

