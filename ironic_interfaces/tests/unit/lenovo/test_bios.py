# SPDX-FileCopyrightText: 2025 VEXXHOST Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for Lenovo BIOS interface.
"""

from typing import Any
from unittest import mock

from ironic.conductor import task_manager
from ironic.drivers.modules.redfish import bios as redfish_bios
from ironic.drivers.modules.redfish import utils as redfish_utils
from ironic.tests.unit.db import base
from ironic.tests.unit.db import utils as db_utils
from ironic.tests.unit.objects import utils as obj_utils

from ironic_interfaces.lenovo import bios

INFO_DICT = db_utils.get_test_redfish_info()


class TestBlueFieldEthernetRedfishBIOS(base.DbTestCase):
    """
    Test cases for BlueFieldEthernetRedfishBIOS.
    """

    def setUp(self) -> None:
        """
        Set up for BlueFieldEthernetRedfishBIOS tests.
        """

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

    @mock.patch.object(bios.BlueFieldEthernetRedfishBIOS, "post_reset", autospec=True)
    @mock.patch.object(redfish_utils, "get_system", autospec=True)
    def test_post_reset_is_called_by_factory_reset(
        self, _: mock.Mock, mock_post_reset: mock.Mock
    ) -> None:
        """
        Ensure that the post_reset method is called when factory_reset is invoked.
        """

        with task_manager.acquire(self.context, self.node.uuid, shared=False) as task:
            task.driver.bios.factory_reset(task)

        mock_post_reset.assert_called_once_with(mock.ANY, task)

    def _call_post_reset(
        self, bios_attributes: dict[str, Any]
    ) -> tuple[task_manager.TaskManager, bios.BlueFieldEthernetRedfishBIOS]:
        """
        Helper method to call post_reset with proper task context.

        :param bios_attributes: Dictionary of BIOS attributes to mock
        :returns: Tuple of (task, bios_interface)
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

    @mock.patch.object(
        bios.BlueFieldEthernetRedfishBIOS, "_clear_reboot_requested", autospec=True
    )
    @mock.patch.object(
        bios.BlueFieldEthernetRedfishBIOS, "apply_configuration", autospec=True
    )
    def test_post_reset_with_mellanox_adapters(
        self, mock_apply_config: mock.Mock, mock_clear_reboot: mock.Mock
    ) -> None:
        """
        Test post_reset when Mellanox adapters are present in BIOS attributes.
        """

        task, bios_interface = self._call_post_reset(
            {
                "MellanoxNetworkAdapter__Slot9PhysicalPort1LogicalPort1_NetworkLinkType": "InfiniBand",
                "MellanoxNetworkAdapter__Slot9PhysicalPort2LogicalPort1_NetworkLinkType": "InfiniBand",
                "SomeOtherSetting": "value",
            }
        )

        expected_settings = [
            {
                "name": "MellanoxNetworkAdapter__Slot9PhysicalPort1LogicalPort1_NetworkLinkType",
                "value": "Ethernet",
            },
            {
                "name": "MellanoxNetworkAdapter__Slot9PhysicalPort2LogicalPort1_NetworkLinkType",
                "value": "Ethernet",
            },
        ]

        mock_clear_reboot.assert_called_once_with(bios_interface, task)
        mock_apply_config.assert_called_once_with(
            bios_interface, task, expected_settings
        )

    @mock.patch.object(redfish_bios.RedfishBIOS, "post_reset", autospec=True)
    def test_post_reset_without_mellanox_adapters(
        self, mock_super_post_reset: mock.Mock
    ) -> None:
        """
        Test post_reset when no Mellanox adapters are present in BIOS attributes.
        """

        task, bios_interface = self._call_post_reset(
            {
                "SomeOtherSetting": "value",
                "AnotherSetting": "another_value",
            }
        )

        mock_super_post_reset.assert_called_once_with(bios_interface, task)
