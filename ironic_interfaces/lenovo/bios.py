# SPDX-FileCopyrightText: 2025 VEXXHOST Inc.
# SPDX-License-Identifier: Apache-2.0

"""
BIOS interface for Lenovo systems with NVIDIA Bluefield cards.
"""

from ironic.conductor import task_manager
from ironic.drivers.modules.redfish import bios, utils


class BlueFieldEthernetRedfishBIOS(bios.RedfishBIOS):
    """
    BIOS interface for systems which use NVIDIA Bluefield cards to ensure
    that after a factory reset, they are configured as Ethernet devices, not
    as Infiniband devices.
    """

    def post_reset(self, task: task_manager.TaskManager) -> None:
        system = utils.get_system(task.node)

        settings = [
            {"name": key, "value": "Ethernet"}
            for key in system.bios.attributes
            if key.startswith("MellanoxNetworkAdapter__Slot")
            and key.endswith("_NetworkLinkType")
        ]

        if not settings:
            return super().post_reset(task)

        self._clear_reboot_requested(task)
        return self.apply_configuration(task, settings)
