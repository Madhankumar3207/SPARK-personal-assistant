import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


class AndroidWellbeingPrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = ET.parse(ROOT / "android/app/src/main/AndroidManifest.xml").getroot()

    def test_no_network_or_accessibility_or_device_admin_permissions(self):
        permissions = {node.get(ANDROID_NS + "name") for node in self.manifest.findall("uses-permission")}
        self.assertNotIn("android.permission.INTERNET", permissions)
        self.assertNotIn("android.permission.BIND_ACCESSIBILITY_SERVICE", permissions)
        self.assertNotIn("android.permission.BIND_DEVICE_ADMIN", permissions)

    def test_usage_access_is_disclosed_and_service_is_not_exported(self):
        permissions = {node.get(ANDROID_NS + "name") for node in self.manifest.findall("uses-permission")}
        self.assertIn("android.permission.PACKAGE_USAGE_STATS", permissions)
        service = self.manifest.find("application/service")
        self.assertIsNotNone(service)
        self.assertEqual(service.get(ANDROID_NS + "exported"), "false")
        self.assertEqual(service.get(ANDROID_NS + "foregroundServiceType"), "specialUse")

    def test_app_does_not_declare_overlay_or_force_stop_capability(self):
        permissions = {node.get(ANDROID_NS + "name") for node in self.manifest.findall("uses-permission")}
        self.assertNotIn("android.permission.SYSTEM_ALERT_WINDOW", permissions)
        self.assertNotIn("android.permission.KILL_BACKGROUND_PROCESSES", permissions)


if __name__ == "__main__":
    unittest.main()
