# 变更记录

本文件采用 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 风格记录项目的重要变更。

## [Unreleased]

### Added

- 新增 `dji-qmi-network`。
- 新增 `doctor`、`connect`、`status` 和 `disconnect` 命令。
- 自动启用 QMI Raw-IP。
- 自动配置 IPv4、路由、MTU 和 DNS。
- 自动处理 ModemManager 冲突。
- 新增安装、改装、联网、故障排查和 FAQ 文档。
- 新增 Issue 和 PR 模板。
- 新增 GitHub Actions 基础检查。

### Changed

- README 重构为项目首页。

### Fixed

- 修复 `connect --force` 覆盖状态文件但未清理旧 WDS 会话的问题。
- 修复联网测试失败后残留 IPv4、路由、DNS 和状态文件的问题。
- 修复 `doctor` 在未注册网络时仍显示关键项目正常的问题。
