from unittest import TestCase
import {{ project_identifier }}.core.core as core


class Test(TestCase):
    def test_execute(self):
        result = core.execute()
        self.assertTrue(result)
