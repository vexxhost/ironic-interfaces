# SPDX-FileCopyrightText: 2025 VEXXHOST Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Hardware type for Lenovo systems using Redfish.
"""

from ironic.drivers import redfish

from ironic_interfaces.lenovo import bios


class LenovoHardware(redfish.RedfishHardware):
    """
    Hardware type for Lenovo systems using Redfish.
    """

    @property
    def supported_bios_interfaces(self):
        """List of supported bios interfaces."""
        return [bios.BlueFieldEthernetRedfishBIOS] + list(
            super().supported_bios_interfaces
        )
