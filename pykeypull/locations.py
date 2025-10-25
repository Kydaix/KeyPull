"""Known locations of keystore and keybox files on Android devices."""

from __future__ import annotations

from typing import Tuple

DEVICE_LOCATIONS: Tuple[str, ...] = (
    "/data/misc/keystore/",
    "/data/misc/keystore/user_0/",
    "/data/misc/keystore/persistent.sqlite",
    "/data/adb/tricky_store/keybox.xml",
    "/mnt/vendor/keystore/",
    "/system/etc/security/keystore/",
    "/vendor/etc/keystore/",
)
