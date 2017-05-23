import logging
from AccessControl import Unauthorized

from five import grok

from docent.hoa.houses.content.hoa_neighborhood import IHOANeighborhood
from zope.component import getMultiAdapter

class View(grok.View):
    grok.context(IHOANeighborhood)
    grok.require("cmf.ManagePortal")
    grok.name('update-home-addresses')

    def render(self):

        return self.updateHomeAddresses()

    def updateHomeAddresses(self):
        """Update all homes tagged in a csv file named: house_block.csv"""
        request = self.request
        context = self.context

        authenticator = getMultiAdapter((context, request), name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized

        context.assignStreetNumbers()
        return request.response.redirect(context.absolute_url())