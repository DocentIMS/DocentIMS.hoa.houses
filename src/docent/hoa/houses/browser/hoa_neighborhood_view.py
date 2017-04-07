import logging
from collections import defaultdict
from operator import itemgetter
from five import grok
from plone import api
from plone.api.exc import MissingParameterError
from plone.protect.utils import addTokenToUrl

from Products.CMFCore.utils import getToolByName
from zope.security import checkPermission
from docent.hoa.houses.app_config import HOUSE_INSPECTION_STATE_TITLES

from docent.hoa.houses.content.hoa_house import IHOAHouse
from docent.hoa.houses.content.hoa_neighborhood import IHOANeighborhood
from docent.hoa.houses.content.hoa_house_inspection import IHOAHouseInspection
from docent.hoa.houses.content.hoa_annual_inspection import IHOAAnnualInspection

grok.templatedir('templates')

class View(grok.View):
    grok.context(IHOANeighborhood)
    grok.require("zope2.View")
    grok.template("neighborhood")

    def update(self):
        """
        get email html structure for all home owners and set them as view attribute
        """
        context = self.context
        context_path = '/'.join(context.getPhysicalPath())
        current_house_brains = context.portal_catalog.searchResults(
                                               path={'query': context_path, 'depth': 2},
                                               object_provides=IHOAHouse.__identifier__,
                                               sort_on="sortable_title",
                                               sort_order="ascending")

        street_dict = defaultdict(list)
        for hi_brain in current_house_brains:
            street = getattr(hi_brain, 'street_number', '')
            address = getattr(hi_brain, 'street_address', '')
            street_address = '%s %s' % (street, address)
            div_lot = getattr(hi_brain, 'id', '')
            home_listing_dict = {'url':hi_brain.getURL(),
                                 'div_lot':div_lot,
                                 'address':street_address,
                                 'map':''}

            street_dict[address].append(home_listing_dict)

        streets = sorted(street_dict.keys())
        for street in streets:
            street_dict[street] = sorted(street_dict[street], key=itemgetter('address'))

        inspections_brains = context.portal_catalog.searchResults(
                                               path={'query': context_path, 'depth': 2},
                                               object_provides=IHOAAnnualInspection.__identifier__,
                                               sort_on="created",
                                               sort_order="ascending")

        current_inspection_state = ''
        if len(inspections_brains) >= 1:
            current_inspection_brain = inspections_brains[0]
            current_inspection_state = current_inspection_brain.review_state

        active_inspection = False
        if current_inspection_state and current_inspection_state != 'closed':
            active_inspection = True

        current_member = api.user.get_current()

        home_admin = api.user.has_permission('HOA: Manage Homes', user=current_member)

        self.home_admin = home_admin
        self.active_inspection = active_inspection
        self.inspections = inspections_brains
        self.streets = streets
        self.street_dict = street_dict

    def getState(self, brain):
        status = brain.review_state

        return HOUSE_INSPECTION_STATE_TITLES.get(status)

    def getTableRowStructure(self, home_listing_dict):
        table_row_structure = ''
        table_row_structure += '<td>%s</td>' % home_listing_dict.get('address')
        table_row_structure += '<td><a href="%s">%s</a></td>' % (home_listing_dict.get('url'),
                                                                 home_listing_dict.get('div_lot'))
        table_row_structure += '<td>%s</td>' % home_listing_dict.get('map')

        return table_row_structure