# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from docent.hoa.houses.testing import DOCENT_HOA_HOUSES_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that docent.hoa.houses is properly installed."""

    layer = DOCENT_HOA_HOUSES_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if docent.hoa.houses is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'docent.hoa.houses'))

    def test_browserlayer(self):
        """Test that IDocentHoaHousesLayer is registered."""
        from docent.hoa.houses.interfaces import (
            IDocentHoaHousesLayer)
        from plone.browserlayer import utils
        self.assertIn(IDocentHoaHousesLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = DOCENT_HOA_HOUSES_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['docent.hoa.houses'])

    def test_product_uninstalled(self):
        """Test if docent.hoa.houses is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'docent.hoa.houses'))

    def test_browserlayer_removed(self):
        """Test that IDocentHoaHousesLayer is removed."""
        from docent.hoa.houses.interfaces import \
            IDocentHoaHousesLayer
        from plone.browserlayer import utils
        self.assertNotIn(IDocentHoaHousesLayer, utils.registered_layers())
