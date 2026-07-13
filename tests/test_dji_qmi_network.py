from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "dji-qmi-network"
LOADER = importlib.machinery.SourceFileLoader("dji_qmi_network", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


def connect_args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "device": None,
        "interface": None,
        "force": False,
        "keep_modemmanager": False,
        "register_timeout": 1,
        "apn": "ctnet",
        "metric": 50,
        "no_test": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class StateFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tempdir.name) / "state.json"
        self.state_patch = mock.patch.object(MODULE, "STATE_FILE", self.state_path)
        self.state_patch.start()

    def tearDown(self) -> None:
        self.state_patch.stop()
        self.tempdir.cleanup()

    def test_load_state_rejects_invalid_json(self) -> None:
        self.state_path.write_text("{invalid", encoding="utf-8")

        with self.assertRaisesRegex(MODULE.ToolError, "联网状态文件损坏"):
            MODULE.load_state()

    def test_load_state_rejects_missing_cid_and_pdh(self) -> None:
        self.state_path.write_text(
            json.dumps({"device": "/dev/cdc-wdm0", "interface": "wwan0"}),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(MODULE.ToolError, "cid, pdh"):
            MODULE.load_state()

    @mock.patch.object(MODULE, "require_command")
    @mock.patch.object(MODULE, "require_root")
    def test_force_cleans_old_state_before_detecting_new_device(
        self,
        _require_root: mock.Mock,
        _require_command: mock.Mock,
    ) -> None:
        old_state = {
            "device": "/dev/cdc-wdm0",
            "interface": "wwan0",
            "cid": 1,
            "pdh": 2,
        }
        self.state_path.write_text(json.dumps(old_state), encoding="utf-8")
        events: list[str] = []

        with (
            mock.patch.object(
                MODULE,
                "cleanup_connection",
                side_effect=lambda *args, **kwargs: events.append("cleanup"),
            ),
            mock.patch.object(
                MODULE,
                "find_qmi_device",
                side_effect=lambda *args, **kwargs: (
                    events.append("detect")
                    or (_ for _ in ()).throw(MODULE.ToolError("停止测试"))
                ),
            ),
        ):
            with self.assertRaisesRegex(MODULE.ToolError, "停止测试"):
                MODULE.command_connect(connect_args(force=True))

        self.assertEqual(events, ["cleanup", "detect"])

    @mock.patch.object(MODULE, "save_state")
    @mock.patch.object(MODULE, "configure_dns", return_value=True)
    @mock.patch.object(MODULE, "configure_interface")
    @mock.patch.object(MODULE, "ensure_raw_ip")
    @mock.patch.object(MODULE, "modemmanager_active", return_value=False)
    @mock.patch.object(MODULE, "find_interface", return_value="wwan0")
    @mock.patch.object(MODULE, "find_qmi_device", return_value="/dev/cdc-wdm0")
    @mock.patch.object(MODULE, "require_command")
    @mock.patch.object(MODULE, "require_root")
    def test_failed_connectivity_test_runs_full_cleanup(
        self,
        _require_root: mock.Mock,
        _require_command: mock.Mock,
        _find_device: mock.Mock,
        _find_interface: mock.Mock,
        _modemmanager_active: mock.Mock,
        _ensure_raw_ip: mock.Mock,
        _configure_interface: mock.Mock,
        _configure_dns: mock.Mock,
        _save_state: mock.Mock,
    ) -> None:
        settings = {
            "address": "10.0.0.2",
            "prefix": 30,
            "gateway": "10.0.0.1",
            "dns": ["1.1.1.1"],
            "mtu": 1500,
        }
        qmi_outputs = [
            "Card state: 'present'",
            "Registration state: 'registered'\nPS: 'attached'",
            "CID: '7'\nPacket data handle: '9'",
            "current settings",
        ]

        with (
            mock.patch.object(MODULE, "qmicli", side_effect=qmi_outputs),
            mock.patch.object(MODULE, "parse_settings", return_value=settings),
            mock.patch.object(MODULE, "test_connection", return_value=(False, None)),
            mock.patch.object(MODULE, "cleanup_connection") as cleanup,
        ):
            with self.assertRaisesRegex(MODULE.ToolError, "已自动回滚"):
                MODULE.command_connect(connect_args())

        cleanup.assert_called_once()
        state = cleanup.call_args.args[0]
        self.assertEqual((state["cid"], state["pdh"]), (7, 9))
        self.assertEqual(state["settings"], settings)
        self.assertTrue(cleanup.call_args.kwargs["restore_modemmanager"])


class DoctorTests(unittest.TestCase):
    def test_unregistered_network_does_not_report_all_normal(self) -> None:
        qmi_outputs = [
            "Model: 'QDC507'",
            "Card state: 'present'\nApplication state: 'ready'",
            "Registration state: 'searching'\nPS: 'detached'",
        ]
        output = io.StringIO()

        with (
            mock.patch.object(MODULE.shutil, "which", return_value="/usr/bin/tool"),
            mock.patch.object(MODULE, "find_qmi_device", return_value="/dev/cdc-wdm0"),
            mock.patch.object(MODULE, "find_interface", return_value="wwan0"),
            mock.patch.object(MODULE, "qmicli", side_effect=qmi_outputs),
            mock.patch.object(MODULE, "modemmanager_active", return_value=False),
            redirect_stdout(output),
        ):
            MODULE.command_doctor(argparse.Namespace(device=None, interface=None))

        text = output.getvalue()
        self.assertIn("基础硬件正常，但当前尚未完成移动网络注册或数据附着", text)
        self.assertNotIn("诊断完成：关键项目正常", text)


if __name__ == "__main__":
    unittest.main()
