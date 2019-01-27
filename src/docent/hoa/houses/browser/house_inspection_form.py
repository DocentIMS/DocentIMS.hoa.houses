from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser

from datetime import datetime
from five import grok

from plone import api
from plone.directives import form
from plone.supermodel.directives import fieldset

from plone.namedfile.field import NamedBlobFile
from Products.statusmessages.interfaces import IStatusMessage
from zope import schema
from zope.interface import invariant, Invalid
from z3c.form import button, field
import logging
from collections import defaultdict
from operator import itemgetter
from five import grok
from plone import api
from plone.api.exc import MissingParameterError, InvalidParameterError
from plone.protect.utils import addTokenToUrl

from Products.CMFCore.utils import getToolByName

from docent.hoa.houses.content.hoa_neighborhood import IHOANeighborhood
from docent.hoa.houses.content.hoa_house import IHOAHouse
from docent.hoa.houses.content.hoa_house_inspection import IHOAHouseInspection
from docent.hoa.houses.content.hoa_annual_inspection import IHOAAnnualInspection

logger = logging.getLogger("Plone")
from docent.hoa.houses import _

grok.templatedir('templates')

def getAnnualInspection():
    portal = api.portal.get()
    annual_inspection_brains = portal.portal_catalog.searchResults(
                                               object_provides=IHOAAnnualInspection.__identifier__,
                                               sort_on="created",
                                               sort_order="descending")
    annual_inspection_brain = None
    if annual_inspection_brains:
        annual_inspection_brain = annual_inspection_brains[0]

    return annual_inspection_brain

def getActiveHomeInspectionId():
    portal = api.portal.get()
    annual_inspection_brains = portal.portal_catalog.searchResults(
                                               object_provides=IHOAAnnualInspection.__identifier__,
                                               sort_on="created",
                                               sort_order="descending")
    active_home_inspection_id = ''
    if annual_inspection_brains:
        annual_inspection_brain = annual_inspection_brains[0]
        ai_obj = annual_inspection_brain.getObject()
        active_home_inspection_id = getattr(ai_obj, 'house_inspection_title')

    return active_home_inspection_id


class IHouseInspectionForm(form.Schema):
    """
    empty no fields
    """

class HouseInspectionForm(form.SchemaForm):
    grok.context(IHOAHouse)
    grok.require("zope2.View")
    grok.template("home_inspection")
    grok.name("home-inspection")

    label = _(u"Home Inspection Form")
    schema = IHouseInspectionForm
    ignoreContext = False

    @button.buttonAndHandler(u"Pass")
    def handlePass(self, action):
        """User cancelled. Redirect back to the front page.
        """
        context = self.context
        annual_inspection_brain = getAnnualInspection()
        ai_review_state = annual_inspection_brain.review_state
        active_home_inspection_id = getActiveHomeInspectionId()

        if not active_home_inspection_id:
            #nothing to do
            api.portal.show_message(message=u"Could not find a home inspection form to update, was the annual "
                                            u"inspection properly initiated?",
                                    request=context.REQUEST,
                                    type='info')
        else:
            current_member = api.user.get_current()
            current_member_id = current_member.getId()
            hi_obj = context.get(active_home_inspection_id)
            current_state = api.content.get_state(obj=hi_obj)
            had_errors = False
            try:
                api.content.transition(obj=hi_obj, transition='pass')
                if ai_review_state == 'initial_inspection':
                    setattr(hi_obj, 'inspected_by_first', current_member_id)
                elif ai_review_state == 'secondary_inspection':
                    setattr(hi_obj, 'inspected_by_second', current_member_id)
                now = datetime.now()
                setattr(hi_obj, 'passed_datetime', now)
                setattr(hi_obj, 'inspection_datetime', now)
            except MissingParameterError:
                had_errors = True
            except InvalidParameterError:
                had_errors = True

            if had_errors:
                home_id = context.getId()
                api.portal.show_message(message=u"An error occurred while updating home %s. Please notify the administrator." % home_id,
                                        request=context.REQUEST,
                                        type='error')
        request = context.REQUEST
        parent_container = context.aq_parent
        response = request.response
        response.redirect('%s/@@walker-assignments' % parent_container.absolute_url())


    @button.buttonAndHandler(u'Fail')
    def handleFail(self, action):
        """
        If fail, transition to first or second failure
        """
        context = self.context
        annual_inspection_brain = getAnnualInspection()
        ai_review_state = annual_inspection_brain.review_state
        active_home_inspection_id = getActiveHomeInspectionId()

        if not active_home_inspection_id:
            #nothing to do
            api.portal.show_message(message=u"Could not find a home inspection form to update, was the annual "
                                            u"inspection properly initiated?",
                                    request=context.REQUEST,
                                    type='info')
        else:
            hi_obj = context.get(active_home_inspection_id)
            current_state = api.content.get_state(obj=hi_obj)
            had_errors = False
            transition_id = ''
            if current_state == 'failed_initial':
                transition_id = 'fail_second'
            elif current_state == 'pending':
                transition_id = 'fail_initial'

            if transition_id:
                try:
                    current_member = api.user.get_current()
                    current_member_id = current_member.getId()
                    api.content.transition(obj=hi_obj, transition=transition_id)
                    now = datetime.now()
                    setattr(hi_obj, 'inspection_datetime', now)
                    if transition_id == 'fail_initial':
                        setattr(hi_obj, 'inspected_by_first', current_member_id)
                    elif transition_id == 'fail_second':
                        setattr(hi_obj, 'inspected_by_second', current_member_id)
                except MissingParameterError:
                    had_errors = True
                except InvalidParameterError:
                    had_errors = True

                if had_errors:
                    home_id = context.getId()
                    api.portal.show_message(message=u"An error occurred while updating home %s. Please notify the administrator." % home_id,
                                            request=context.REQUEST,
                                            type='error')
                    request = context.REQUEST
                    parent_container = context.aq_parent
                    response = request.response
                    return response.redirect('%s/@@walker-assignments' % parent_container.absolute_url())

                request = context.REQUEST
                parent_container = context.aq_parent
                response = request.response
                return response.redirect('%s/edit' % hi_obj.absolute_url())

            else:
                home_id = context.getId()
                api.portal.show_message(message=u"The home inspection was not in a state we could "
                                                u"transition from." % home_id,
                                        request=context.REQUEST,
                                        type='error')
                request = context.REQUEST
                parent_container = context.aq_parent
                response = request.response
                return response.redirect('%s/@@walker-assignments' % parent_container.absolute_url())
