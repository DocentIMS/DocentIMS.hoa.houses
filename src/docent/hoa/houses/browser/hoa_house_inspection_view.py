import logging
from five import grok
from plone import api
from plone.api.exc import MissingParameterError
from plone.protect.utils import addTokenToUrl
from docent.hoa.houses.app_config import HOME_INSPECTION_STATE_TITLES
from docent.hoa.houses.content.hoa_house import IHOAHouse
from docent.hoa.houses.content.hoa_house_inspection import IHOAHouseInspection
from docent.hoa.houses.content.hoa_annual_inspection import IHOAAnnualInspection
from docent.hoa.houses.content.hoa_house_inspection import IHOAHOUSEINSPECTION_FIELDSETS

grok.templatedir('templates')

SECTION_TITLES = {'roof': 'Roof',
                  'gutters': 'Gutters',
                  'exterior_paint': 'Exterior Paint',
                  'decks': 'Decks',
                  'entry_way': 'Entry Way',
                  'paved_surfaces': 'Paved Surfaces',
                  'landscaping': 'Landscaping',
                  'general_maintenance': 'General Maintenance'}

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
        passed_datetime = getattr(context, 'passed_datetime', None)
        if passed_datetime:
            self.passed_datetime = passed_datetime.strftime('%B %-d, %Y %H:%M')
        else:
            self.passed_datetime = ''

        inspection_datetime = getattr(context, 'inspection_datetime', None)
        if inspection_datetime:
            self.inspection_datetime = inspection_datetime.strftime('%B %-d, %Y %H:%M')
        else:
            self.inspection_datetime = ''

        self.sections = IHOAHOUSEINSPECTION_FIELDSETS

        home_container = context.aq_parent
        self.home_container = home_container

        neighborhood_container = home_container.aq_parent
        self.neighborhood_container = neighborhood_container

        self.retractable = False
        if api.content.get_state(obj=context) != 'pending':
            self.retractable = True

    # def getRewalkCondition(self, rewalk_condition):
    #     if rewalk_condition:
    #         return 'YES'
    #
    #     return 'NO'

    def getTransitionURL(self):
        url = "%s/content_status_modify?workflow_action=retract" % self.context.absolute_url()
        return url
        #return addTokenToUrl(url)

    def getAddress(self):
        return self.home_container.get_address()

    def getAssignmentsURL(self):
        return "%s/@@walker-assignments" % self.neighborhood_container.absolute_url()

    def getSectionTitle(self, section):
        return SECTION_TITLES[section]

    def hasSectionFailures(self, section):
        context = self.context
        action_required = getattr(context, '%s_action_required' % section)
        text = getattr(context, '%s_text' % section)
        if not action_required and not text:
            return False
        return True

    def getSectionAction(self, section):
        context = self.context
        action_required = getattr(context, '%s_action_required' % section)
        if action_required:
            return action_required.title()

        return 'None'

    def getSectionText(self, section):
        context = self.context
        text = getattr(context, '%s_text' % section)
        if text:
            return text

        return ''

    def getInitialImage(self, section):
        context = self.context
        image = getattr(context, '%s_image' % section)
        if image:
            return '%s_image' % section

        return None

    def getRewalkCondition(self, section):
        context = self.context
        cond_remains = getattr(context, '%s_cond_remains' % section)
        if cond_remains:
            return 'YES'

        return 'NO'

    def getSectionRewalkText(self, section):
        context = self.context
        rewalk_text = getattr(context, '%s_rewalk_text' % section)
        if rewalk_text:
            return rewalk_text

        return ''

    def getRewalkImage(self, section):
        context = self.context
        rewalk_image = getattr(context, '%s_rewalk_image' % section)
        if rewalk_image:
            return '%s_rewalk_image' % section

        return None

    # def getSectionFailures(self, section):
    #     context = self.context
    #     cond_remains = getattr(context, '%s_cond_remains' % section)
    #     action_required = getattr(context, '%s_action_required' % section)
    #     text = getattr(context, '%s_text' % section)
    #     rewalk_text = getattr(context, '%s_rewalk_text' % section)
    #     image = getattr(context, '%s_image' % section)
    #     rewalk_image = getattr(context, '%s_rewalk_image' % section)


