# SPDX-CopyrightText: 2025 VEXXHOST Inc.
# SPDX-License-Identifier: Apache-2.0

from oslo_service import backend

backend.init_backend(backend.BackendType.THREADING)
