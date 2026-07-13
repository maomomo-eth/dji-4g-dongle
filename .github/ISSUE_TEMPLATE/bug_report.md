---
name: 故障反馈
about: 报告模块识别、改装或联网问题
title: "[Bug] "
labels: bug
assignees: ""
---

## 问题描述

请说明你遇到的问题、期望结果和实际结果。

## 环境信息

- 系统及版本：
- 内核版本：
- 模块型号：
- 固件版本：
- 原始/当前 USB ID：
- 运营商与 APN：

## 诊断输出

请粘贴以下命令输出，并注意遮盖 IMEI、手机号等敏感信息：

```bash
sudo dji-qmi-network doctor
sudo dji-qmi-network status
lsusb
lsusb -t
ip addr
ip route
```

## 错误日志

```text
在此粘贴错误信息
```

## 已尝试的方法

请列出已经尝试过的操作。