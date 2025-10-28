# SPDX-FileCopyrightText: 2025 VEXXHOST Inc.
# SPDX-License-Identifier: Apache-2.0

from ironic.drivers.modules.redfish import bios
from ironic.drivers.modules.redfish import utils


class BlueFieldEthernetRedfishBIOS(bios.RedfishBIOS):
    """
    BIOS interface for systems which use NVIDIA Bluefield cards to ensure
    that after a factory reset, they are configured as Ethernet devices, not
    as Infiniband devices.
    """

    def post_reset(self, task):
        system = utils.get_system(task.node)

        print(system.bios)
