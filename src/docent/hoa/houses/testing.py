# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import docent.hoa.houses


class DocentHoaHousesLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=docent.hoa.houses)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'docent.hoa.houses:default')


DOCENT_HOA_HOUSES_FIXTURE = DocentHoaHousesLayer()


DOCENT_HOA_HOUSES_INTEGRATION_TESTING = IntegrationTesting(
    bases=(DOCENT_HOA_HOUSES_FIXTURE,),
    name='DocentHoaHousesLayer:IntegrationTesting'
)


DOCENT_HOA_HOUSES_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(DOCENT_HOA_HOUSES_FIXTURE,),
    name='DocentHoaHousesLayer:FunctionalTesting'
)


DOCENT_HOA_HOUSES_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        DOCENT_HOA_HOUSES_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='DocentHoaHousesLayer:AcceptanceTesting'
)
