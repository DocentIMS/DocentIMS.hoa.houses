# -*- coding: utf-8 -*-
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from docent.hoa.houses.interfaces import Ihouse
from docent.hoa.houses.testing import DOCENT_HOA_HOUSES_INTEGRATION_TESTING  # noqa
from zope.component import createObject
from zope.component import queryUtility

import unittest


class houseIntegrationTest(unittest.TestCase):

    layer = DOCENT_HOA_HOUSES_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_schema(self):
        fti = queryUtility(IDexterityFTI, name='house')
        schema = fti.lookupSchema()
        self.assertEqual(Ihouse, schema)

    def test_fti(self):
        fti = queryUtility(IDexterityFTI, name='house')
        self.assertTrue(fti)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI, name='house')
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(Ihouse.providedBy(obj))

    def test_adding(self):
        obj = api.content.create(
            container=self.portal,
            type='house',
            id='house',
        )
        self.assertTrue(Ihouse.providedBy(obj))
