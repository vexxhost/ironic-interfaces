# SPDX-FileCopyrightText: 2025 VEXXHOST Inc.
# SPDX-License-Identifier: Apache-2.0

from unittest import mock

from ironic.conductor import task_manager
from ironic.drivers.modules.redfish import bios as redfish_bios
from ironic.drivers.modules.redfish import utils as redfish_utils
from ironic.tests.unit.db import base
from ironic.tests.unit.db import utils as db_utils
from ironic.tests.unit.objects import utils as obj_utils

from ironic_interfaces.lenovo import bios

INFO_DICT = db_utils.get_test_redfish_info()
MELLANOX_PORT1_ATTR = (
    "MellanoxNetworkAdapter__Slot9PhysicalPort1LogicalPort1_NetworkLinkType"
)
MELLANOX_PORT2_ATTR = (
    "MellanoxNetworkAdapter__Slot9PhysicalPort2LogicalPort1_NetworkLinkType"
)


class TestBlueFieldEthernetRedfishBIOS(base.DbTestCase):
    def setUp(self):
        super(TestBlueFieldEthernetRedfishBIOS, self).setUp()
        self.config(
            enabled_bios_interfaces=["redfish-bluefield-ethernet"],
            enabled_hardware_types=["lenovo"],
            enabled_power_interfaces=["redfish"],
            enabled_management_interfaces=["redfish"],
        )
        self.node = obj_utils.create_test_node(
            self.context, driver="lenovo", driver_info=INFO_DICT
        )

    def _call_post_reset(self, bios_attributes):
        """Helper method to call post_reset with proper task context.

        Args:
            bios_attributes: Dictionary of BIOS attributes to mock
        """
        with mock.patch.object(
            redfish_utils, "get_system", autospec=True
        ) as mock_get_system:
            mock_get_system.return_value.bios.attributes = bios_attributes

            bios_interface = bios.BlueFieldEthernetRedfishBIOS()
            with task_manager.acquire(
                self.context, self.node.uuid, shared=False
            ) as task:
                bios_interface.post_reset(task)
                return task, bios_interface

    @mock.patch.object(bios.BlueFieldEthernetRedfishBIOS, "post_reset", autospec=True)
    @mock.patch.object(redfish_utils, "get_system", autospec=True)
    def test_post_reset_is_called_by_factory_reset(
        self, mock_get_system, mock_post_reset
    ):
        with task_manager.acquire(self.context, self.node.uuid, shared=False) as task:
            task.driver.bios.factory_reset(task)

        mock_post_reset.assert_called_once_with(mock.ANY, task)

    @mock.patch.object(
        bios.BlueFieldEthernetRedfishBIOS, "_clear_reboot_requested", autospec=True
    )
    @mock.patch.object(
        bios.BlueFieldEthernetRedfishBIOS, "apply_configuration", autospec=True
    )
    def test_post_reset_with_mellanox_adapters(
        self, mock_apply_config, mock_clear_reboot
    ):
        task, bios_interface = self._call_post_reset(
            {
                MELLANOX_PORT1_ATTR: "InfiniBand",
                MELLANOX_PORT2_ATTR: "InfiniBand",
                "SomeOtherSetting": "value",
            }
        )

        expected_settings = [
            {"name": MELLANOX_PORT1_ATTR, "value": "Ethernet"},
            {"name": MELLANOX_PORT2_ATTR, "value": "Ethernet"},
        ]

        mock_clear_reboot.assert_called_once_with(bios_interface, task)
        mock_apply_config.assert_called_once_with(
            bios_interface, task, expected_settings
        )

    @mock.patch.object(redfish_bios.RedfishBIOS, "post_reset", autospec=True)
    def test_post_reset_without_mellanox_adapters(self, mock_super_post_reset):
        task, bios_interface = self._call_post_reset(
            {
                "SomeOtherSetting": "value",
                "AnotherSetting": "another_value",
            }
        )

        mock_super_post_reset.assert_called_once_with(bios_interface, task)
