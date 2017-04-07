import logging
from five import grok
from plone import api
from plone.api.exc import MissingParameterError
from plone.protect.utils import addTokenToUrl
from docent.hoa.houses.app_config import HOME_INSPECTION_STATE_TITLES
from docent.hoa.houses.content.hoa_house import IHOAHouse
from docent.hoa.houses.content.hoa_house_inspection import IHOAHouseInspection
from docent.hoa.houses.content.hoa_annual_inspection import IHOAAnnualInspection

grok.templatedir('templates')

def getWalkerAndEmailStructureById(member_id):
    if not member_id:
        return ''
    try:
        member_data = api.user.get(userid=member_id)
        fullname = member_data.getProperty('fullname')
        email = member_data.getProperty('email')
    except MissingParameterError:
        return '<em>Unknown Member</em>'

    return "<a href='mailto:%s'>%s</a>" % (email, fullname)

class View(grok.View):
    grok.context(IHOAHouseInspection)
    grok.require("zope2.View")
    grok.template("hoa_house_inspection")

    def update(self):
        """
        get email html structure for all home owners and set them as view attribute
        """
        context = self.context
        inspected_by_first = getattr(context, 'inspected_by_first', '')
        self.inspected_by_first = getWalkerAndEmailStructureById(inspected_by_first)
        inspected_by_second = getattr(context, 'inspected_by_second', '')
        self.inspected_by_second = getWalkerAndEmailStructureById(inspected_by_second)

        self.flowerpotsErrors = getattr(context, 'flowerpots_text', '')
        self.paintErrors = getattr(context, 'paint_text', '')
        self.sidewalk_driveErrors = getattr(context, 'sidewalk_drive_text', '')
        self.general_maintenanceErrors = getattr(context, 'general_maintenance_text', '')
        self.stepsErrors = getattr(context, 'steps_text', '')
        self.decks_patioErrors = getattr(context, 'decks_patio_text', '')
        self.passed_datetime = getattr(context, 'passed_datetime', None)

        home_container = context.aq_parent
        self.home_container = home_container

        neighborhood_container = home_container.aq_parent
        self.neighborhood_container = neighborhood_container

    def getRewalkCondition(self, rewalk_condition):
        if rewalk_condition:
            return 'YES'

        return 'NO'

    def getAddress(self):
        return self.home_container.get_address()

    def getAssignmentsURL(self):
        return "%s/@@walker-assignments" % self.neighborhood_container.absolute_url()