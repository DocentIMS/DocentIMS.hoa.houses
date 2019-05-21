import logging
from datetime import date

from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser
import transaction

from plone.namedfile.file import NamedBlobFile
import csv
from cStringIO import StringIO

import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from collections import Counter
from plone import api
from plone.dexterity.content import Container
from plone.directives import form
from plone.indexer import indexer
from plone.namedfile.field import NamedBlobImage
from plone.supermodel.directives import fieldset
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.interface import provider, invariant, Invalid
from zope.schema.interfaces import IContextAwareDefaultFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from z3c.form.browser.radio import RadioFieldWidget

from docent.hoa.houses.content.hoa_house import IHOAHouse
from docent.hoa.houses.content.hoa_house_inspection import IHOAHouseInspection

from docent.hoa.houses.registry import IHOAHomeLookupRegistry
from docent.hoa.houses.app_config import (HOME_ROLE_TO_ATTRIBUTE_LOOKUP_DICT,
                                          LOT_DIVISION_DICT,
                                          WALKERS_GROUP_IDS,
                                          IHOAHOUSEINSPECTION_FIELDSETS,
                                          IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT,
                                          REQUIRED_ACTION_DICT)
from docent.hoa.houses.registry import (addHomeToLookupRegistry,
                                        removeHomeFromLookupRegistry,
                                        clearAllHomesForMember,
                                        addCurrentHomeRoles)

from docent.hoa.houses import _

logger = logging.getLogger("Plone")

group_numbers_vocab = SimpleVocabulary([SimpleTerm(value=3, title=_(u'3')),
                                  SimpleTerm(value=4, title=_(u'4')),
                                  SimpleTerm(value=5, title=_(u'5')), ])

def computeTitle():
    date_obj = date.today()
    date_str = date_obj.strftime('%Y')

    return u'Annual Inspection %s' % date_str

class DoubleMemberInGroup(Invalid):
    __doc__ = _(u"You can't have the same member listed twice in a weed walk group.")


class MinimumGroups(Invalid):
    __doc__ = _(u"Groups A, B, and C must have week walkers assigned.")


class IHOAAnnualInspection(form.Schema):
    """
    """

    form.mode(title='hidden')
    title = schema.TextLine(
        title=_(u"Title"),
        required=False,
        defaultFactory=computeTitle,
    )

    form.mode(house_inspection_title='hidden')
    house_inspection_title = schema.TextLine(
        title=_(u"House Inspection Title"),
        required=False,
    )

    start_date = schema.Date(
        title=_(u"Start Date"),
        description=_(u""),
    )

    end_date = schema.Date(
        title=_(u"End Date"),
        description=_(u""),
    )

#    form.mode(initial_email_sent='hidden')
    initial_email_sent = schema.Bool(
        title = _(u'Initial Email Sent'),
        description = _(u''),
        default=False,
        required=False)

    # form.widget(pic_req=RadioFieldWidget)
    # pic_req = schema.Choice(
    #     title=_(u'Picture Rqd if Failed?'),
    #     description=_(u''),
    #     source=SimpleVocabulary([SimpleTerm(value=True,
    #                                         title=u"Yes"),
    #                              SimpleTerm(value=False,
    #                                         title=U"No")])
    # )

    form.mode(house_failure_log='hidden')
    house_failure_log = schema.Dict(
        title=_(u'Homes Sent Initial Failure Notices'),
        description=_(u"Emails sent to the following home owners."),
        key_type=schema.ASCIILine(),
        value_type=schema.List(value_type=schema.ASCIILine()),
        required=False,
    )

    form.mode(house_pass_log='hidden')
    house_pass_log = schema.Dict(
        title=_(u'Homes Sent Initial Pass Notices'),
        description=_(u"Emails sent to the following home owners."),
        key_type=schema.ASCIILine(),
        value_type=schema.List(value_type=schema.ASCIILine()),
        required=False,
    )

    form.mode(csv_pass_log='hidden')
    csv_pass_log = schema.Dict(
        title=_(u'Homes Sent Initial Pass Notices'),
        description=_(u"Emails sent to the following home owners."),
        key_type=schema.ASCIILine(),
        value_type=schema.List(value_type=schema.ASCIILine()),
        required=False,
    )

    form.mode(rewalk_failure_log='hidden')
    rewalk_failure_log = schema.Dict(
        title=_(u'Homes Sent Re-Inspection Pass Notices'),
        description=_(u"Emails sent to the following home owners."),
        key_type=schema.ASCIILine(),
        value_type=schema.List(value_type=schema.ASCIILine()),
        required=False,
    )

    form.mode(rewalk_pass_log='hidden')
    rewalk_pass_log = schema.Dict(
        title=_(u'Homes Sent Re-Inspection Pass Notices'),
        description=_(u"Emails sent to the following home owners."),
        key_type=schema.ASCIILine(),
        value_type=schema.List(value_type=schema.ASCIILine()),
        required=False,
    )

    # number_of_groups = schema.Choice(
    #     title=_(u"Number of Groups"),
    #     description=_(u""),
    #     vocabulary=group_numbers_vocab,
    #     required=True,
    # )

    fieldset('team_a',
        label=u'Team A',
        description=u'',
        fields=['group_a_member_one',
                'group_a_member_two', ]
    )

    group_a_member_one = schema.Choice(
        title=_(u"Group A Member One"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    group_a_member_two = schema.Choice(
        title=_(u"Group A Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    fieldset('team_b',
        label=u'Team B',
        description=u'',
        fields=['group_b_member_one',
                'group_b_member_two', ]
    )

    group_b_member_one = schema.Choice(
        title=_(u"Group B Member One"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    group_b_member_two = schema.Choice(
        title=_(u"Group B Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    fieldset('team_c',
        label=u'Team C',
        description=u'',
        fields=['group_c_member_one',
                'group_c_member_two', ]
    )

    group_c_member_one = schema.Choice(
        title=_(u"Group C Member One"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    group_c_member_two = schema.Choice(
        title=_(u"Group C Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    fieldset('team_d',
        label=u'Team D',
        description=u'',
        fields=['group_d_member_one',
                'group_d_member_two', ]
    )

    group_d_member_one = schema.Choice(
        title=_(u"Group D Member One"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    group_d_member_two = schema.Choice(
        title=_(u"Group D Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    # fieldset('team_e',
    #     label=u'Team E',
    #     description=u'',
    #     fields=['group_e_member_one',
    #             'group_e_member_two', ]
    # )
    #
    # group_e_member_one = schema.Choice(
    #     title=_(u"Group E Member One"),
    #     description=_(u""),
    #     vocabulary=u'docent.hoa.walkers',
    #     required=False,
    #     default='',
    # )
    #
    # group_e_member_two = schema.Choice(
    #     title=_(u"Group E Member Two"),
    #     description=_(u""),
    #     vocabulary=u'docent.hoa.walkers',
    #     required=False,
    #     default='',
    # )


class HOAAnnualInspection(Container):
    """
    """

    def after_object_added_processor(self, context, event):
        self.generate_house_inspection_title()
        self.add_walkers_to_groups()
        context_state = api.content.get_state(obj=self)
        if context_state not in ['draft', 'closed']:
            self.assign_security()

    def after_edit_processor(self):
        self.add_walkers_to_groups()
        context_state = api.content.get_state(obj=self)
        if context_state not in ['draft', 'closed']:
            self.assign_security()

    def after_transition_processor(self, event):
        context_state = api.content.get_state(obj=self)
        if context_state == 'initial_inspection':
            self.propagate_house_inspections()
            self.assign_security()
            self.emailInspectors()

        if context_state == 'secondary_inspection':
            self.sendEmailNotices()
            logger.info('Emails Sent')
            self.createCSVFiles()
            logger.info('CSV Files Created')
        if context_state == 'closed':
            self.sendEmailNotices(rewalk=True)
            logger.info('Emails Sent')
            self.createCSVFiles(rewalk=True)
            logger.info('CSV Files Created')

    def checkLastInspection(self):
        context_state = api.content.get_state(obj=self)
        sm = getSecurityManager()
        role = 'Manager'
        tmp_user = BaseUnrestrictedUser(sm.getUser().getId(), '', [role], '')
        portal= api.portal.get()
        tmp_user = tmp_user.__of__(portal.acl_users)
        newSecurityManager(None, tmp_user)
        try:
            if context_state == 'initial_inspection':
                if self.verifyFirstInspectionComplete(guard=False):
                    #send email
                    logger.info('Initial Inspection Ready to Close, email sent to board')
                    api.portal.send_email(recipient='board@themeadowsofredmond.org',
                                          subject='The Meadows Annual Property Initial Inspection is complete.',
                                          body='All homes have been inspected - HAL :)')

            elif context_state == 'secondary_inspection':
                if self.verifySecondInspectionComplete(guard=False):
                    #send_email
                    logger.info('Re-Inspection Ready to Close, email sent to board')
                    api.portal.send_email(recipient='board@themeadowsofredmond.org',
                                          subject='The Meadows Annual Property Re-Inspection is complete.',
                                          body='All homes have been inspected - HAL :)')
            setSecurityManager(sm)
        except Exception as e:
            setSecurityManager(sm)
            logger.warn('HOA Annual Inspection Check Last Inspection failed.')

    def add_walkers_to_groups(self):
        for g_id in WALKERS_GROUP_IDS:
            current_members = api.user.get_users(groupname=g_id)
            for a_member in current_members:
                api.group.remove_user(groupname=g_id, user=a_member)

        group_a_member_one = getattr(self, 'group_a_member_one', None)
        group_a_member_two = getattr(self, 'group_a_member_two', None)
        group_b_member_one = getattr(self, 'group_b_member_one', None)
        group_b_member_two = getattr(self, 'group_b_member_two', None)
        group_c_member_one = getattr(self, 'group_c_member_one', None)
        group_c_member_two = getattr(self, 'group_c_member_two', None)
        group_d_member_one = getattr(self, 'group_d_member_one', None)
        group_d_member_two = getattr(self, 'group_d_member_two', None)
        # group_e_member_one = getattr(self, 'group_e_member_one', None)
        # group_e_member_two = getattr(self, 'group_e_member_two', None)

        if group_a_member_one:
            api.group.add_user(groupname='walkers_a', username=group_a_member_one)
            api.group.add_user(groupname='division_map_one', username=group_a_member_one)
        if group_a_member_two:
            api.group.add_user(groupname='walkers_a', username=group_a_member_two)
            api.group.add_user(groupname='division_map_one', username=group_a_member_two)
        if group_b_member_one:
            api.group.add_user(groupname='walkers_b', username=group_b_member_one)
            api.group.add_user(groupname='division_map_one', username=group_b_member_one)
        if group_b_member_two:
            api.group.add_user(groupname='walkers_b', username=group_b_member_two)
            api.group.add_user(groupname='division_map_one', username=group_b_member_two)
        if group_c_member_one:
            api.group.add_user(groupname='walkers_c', username=group_c_member_one)
            api.group.add_user(groupname='division_map_two', username=group_c_member_one)
        if group_c_member_two:
            api.group.add_user(groupname='walkers_c', username=group_c_member_two)
            api.group.add_user(groupname='division_map_two', username=group_c_member_two)
        if group_d_member_one:
            api.group.add_user(groupname='walkers_d', username=group_d_member_one)
            api.group.add_user(groupname='division_map_two', username=group_d_member_one)
        if group_d_member_two:
            api.group.add_user(groupname='walkers_d', username=group_d_member_two)
            api.group.add_user(groupname='division_map_two', username=group_d_member_two)
        # if group_e_member_one:
        #     api.group.add_user(groupname='walkers_e', username=group_e_member_one)
        # if group_e_member_two:
        #     api.group.add_user(groupname='walkers_e', username=group_e_member_two)


    def getNumberOfGroups(self):
        context = self
        group_a_member_one = getattr(self, 'group_a_member_one', None)
        group_a_member_two = getattr(self, 'group_a_member_two', None)
        group_b_member_one = getattr(self, 'group_b_member_one', None)
        group_b_member_two = getattr(self, 'group_b_member_two', None)
        group_c_member_one = getattr(self, 'group_c_member_one', None)
        group_c_member_two = getattr(self, 'group_c_member_two', None)
        group_d_member_one = getattr(self, 'group_d_member_one', None)
        group_d_member_two = getattr(self, 'group_d_member_two', None)
        # group_e_member_one = getattr(self, 'group_e_member_one', None)
        # group_e_member_two = getattr(self, 'group_e_member_two', None)

        number_of_groups = 0
        if group_a_member_one or group_a_member_two:
            number_of_groups += 1
        if group_b_member_one or group_b_member_two:
            number_of_groups += 1
        if group_c_member_one or group_c_member_two:
            number_of_groups += 1
        if group_d_member_one or group_d_member_two:
            number_of_groups += 1
        # if group_e_member_one or group_e_member_two:
        #     number_of_groups += 1

        return number_of_groups


    def assign_security(self):
        context = self
        parent_container = context.aq_parent
        if parent_container.portal_type != "hoa_neighborhood":
            #woah something went wrong
            return
        #number_of_groups = getattr(context, 'number_of_groups', 3)
        number_of_groups = context.getNumberOfGroups()
        lot_division_dict = LOT_DIVISION_DICT.get(number_of_groups)
        for walker_group_id in lot_division_dict:
            homes_assigned_by_id = lot_division_dict.get(walker_group_id)
            for home_id in homes_assigned_by_id:
                home_obj = parent_container.get(home_id)
                if home_obj:
                    #clear previous group roles
                    for wg_id in WALKERS_GROUP_IDS:
                        api.group.revoke_roles(groupname=wg_id,
                                               roles=['Reader'],
                                               obj=home_obj)
                    #home_obj.manage_delLocalRoles(WALKERS_GROUP_IDS)
                    #set new role
                    api.group.grant_roles(groupname=walker_group_id,
                                          roles=['Reader'],
                                          obj=home_obj)
                    home_obj.reindexObjectSecurity()
                    home_inspections = home_obj.listFolderContents(contentFilter={"portal_type":"hoa_house_inspection",
                                                                         "sort_on":"created",
                                                                         "sort_order":"ascending"})
                    for home_insp in home_inspections:
                        for wg_id in WALKERS_GROUP_IDS:
                            api.group.revoke_roles(groupname=wg_id,
                                                   roles=['Editor', 'Reviewer'],
                                                   obj=home_insp)
                            home_insp.reindexObjectSecurity()

                    house_inspection_title = getattr(context, 'house_inspection_title', '')
                    current_hi = getattr(home_obj, house_inspection_title, None)
                    if current_hi:
                        api.group.grant_roles(groupname=walker_group_id,
                                              roles=['Editor', 'Reviewer'],
                                              obj=current_hi)
                        current_hi.reindexObjectSecurity()


    def generate_house_inspection_title(self):
        today = date.today()
        setattr(self, 'house_inspection_title', today.strftime('%Y'))

    def propagate_house_inspections(self):
        context = self
        parent_container = context.aq_parent
        pc_path = '/'.join(parent_container.getPhysicalPath())
        catalog = getToolByName(parent_container, 'portal_catalog')
        house_brains = catalog(path={'query': pc_path, 'depth': 1},
                               object_provides=IHOAHouse.__identifier__,)
        house_inspection_title = getattr(self, 'house_inspection_title', '')
        if not house_inspection_title:
            today = date.today()
            house_inspection_title = today.strftime('%Y')

        added_inspections = 0
        for house_brain in house_brains:
            house_obj = house_brain.getObject()
            house_obj_title = getattr(house_obj, 'title', 'unknown house')
            if house_inspection_title not in house_obj:
                new_insp = api.content.create(container=house_obj,
                                   type='hoa_house_inspection',
                                   id=house_inspection_title,
                                   title=house_inspection_title,
                                   safe_id=True)
                setattr(new_insp, 'title', house_inspection_title)
                added_inspections += 1

        api.portal.show_message(message=u"%s houses prepared for annual inspection." % added_inspections,
                                request=context.REQUEST,
                                type='info')

    def verifyFirstInspectionComplete(self, guard=True):
        context = self
        parent_container = context.aq_parent
        parent_container_path = '/'.join(parent_container.getPhysicalPath())
        current_inspection_brains = context.portal_catalog.searchResults(
                   path={'query': parent_container_path, 'depth': 3},
                   object_provides=IHOAHouseInspection.__identifier__,
                   review_state='pending')

        if current_inspection_brains:
            house_inspection_title = getattr(context, 'house_inspection_title', '')
            current_inspections = []
            [current_inspections.append(i) for i in current_inspection_brains if i.getId == house_inspection_title]
            pending_inspections = len(current_inspections)
            portal_msg = ""
            if pending_inspections > 20:
                portal_msg += "There are %s homes remaining to inspect." % pending_inspections
            else:
                portal_msg += "The following homes have not been inspected: "
                #portal_msg += '<a href="%s">%s</a>' %(current_inspection_brains[0].getURL(), current_inspection_brains[0].Title)
                ci_brain_zero = current_inspection_brains[0]
                ci_brain_zero_obj = ci_brain_zero.getObject()
                ci_brain_zero_parent = ci_brain_zero_obj.aq_parent
                #portal_msg += '%s' % current_inspection_brains[0].Title
                portal_msg += '%s' % ci_brain_zero_parent.title

                for ci_brain in current_inspection_brains[1:]:
                    #portal_msg += ', <a href="%s">%s</a>' % (ci_brain.getURL(), ci_brain.Title)
                    ci_brain_obj = ci_brain.getObject()
                    ci_brain_parent = ci_brain_obj.aq_parent
                    portal_msg += ', %s' % ci_brain_parent.title
                    #portal_msg += ', %s' % ci_brain.Title

            if guard:
                api.portal.show_message(message=portal_msg,
                                        request=context.REQUEST,
                                        type='info')
            else:
                if len(current_inspection_brains) == 1:
                    last_brain = current_inspection_brains[0]
                    last_brain_obj = last_brain.getObject()
                    lbo_state = api.content.get_state(obj=last_brain_obj)
                    if lbo_state in ['passed', 'failed_initial']:
                        return True

            return False

        return True

    def verifyWalkersAssigned(self):
        context = self
        group_a_member_one = getattr(self, 'group_a_member_one', None)
        group_a_member_two = getattr(self, 'group_a_member_two', None)
        group_b_member_one = getattr(self, 'group_b_member_one', None)
        group_b_member_two = getattr(self, 'group_b_member_two', None)
        group_c_member_one = getattr(self, 'group_c_member_one', None)
        group_c_member_two = getattr(self, 'group_c_member_two', None)
        group_d_member_one = getattr(self, 'group_d_member_one', None)
        group_d_member_two = getattr(self, 'group_d_member_two', None)
        # group_e_member_one = getattr(self, 'group_e_member_one', None)
        # group_e_member_two = getattr(self, 'group_e_member_two', None)

        team_a = False
        team_b = False
        team_c = False
        team_d = False

        if group_a_member_one and group_a_member_two:
            team_a = True
        else:
            api.portal.show_message(message=u"Team A must have two walkers.",
                                    request=context.REQUEST,
                                    type='warning')
            return False

        if group_b_member_one and group_b_member_two:
            team_b = True
        else:
            api.portal.show_message(message=u"Team B must have two walkers.",
                                    request=context.REQUEST,
                                    type='warning')
            return False

        if group_c_member_one and group_c_member_two:
            team_c = True
        else:
            api.portal.show_message(message=u"Team C must have two walkers.",
                                    request=context.REQUEST,
                                    type='warning')
            return False

        three_teams = False
        if team_a and team_b and team_c:
            three_teams = True

        if group_d_member_one or group_d_member_two:
            team_d = True
            if not three_teams:
                api.portal.show_message(message=u"You must configure Teams A, B, and C before Teams D or E.",
                                    request=context.REQUEST,
                                    type='warning')
                return False

        # if group_e_member_one or group_e_member_two:
        #     if not three_teams:
        #         api.portal.show_message(message=u"You must configure Teams A, B, and C before Teams D or E.",
        #                             request=context.REQUEST,
        #                             type='warning')
        #         return False
        #     if not team_d:
        #         api.portal.show_message(message=u"You must configure Team D before Team E.",
        #                             request=context.REQUEST,
        #                             type='warning')
        #         return False

        return True

    def verifySecondInspectionComplete(self, guard=True):
        context = self
        parent_container = context.aq_parent
        parent_container_path = '/'.join(parent_container.getPhysicalPath())
        pending_inspection_brains = context.portal_catalog.searchResults(
                   path={'query': parent_container_path, 'depth': 3},
                   object_provides=IHOAHouseInspection.__identifier__,
                   review_state='pending')
        current_inspection_brains = context.portal_catalog.searchResults(
                   path={'query': parent_container_path, 'depth': 3},
                   object_provides=IHOAHouseInspection.__identifier__,
                   review_state='failed_initial')

        active_inspection_brains = pending_inspection_brains + current_inspection_brains

        if active_inspection_brains:
            house_inspection_title = getattr(context, 'house_inspection_title', '')
            current_inspections = []
            [current_inspections.append(i) for i in active_inspection_brains if i.getId == house_inspection_title]
            pending_inspections = len(current_inspections)
            pending_inspections = len(active_inspection_brains)
            portal_msg = ""
            if pending_inspections > 20:
                portal_msg += "There are %s homes remaining to inspect." % pending_inspections
            else:
                portal_msg += "The following homes have not been inspected: "
                #portal_msg += '<a href="%s">%s</a>' %(current_inspection_brains[0].getURL(), current_inspection_brains[0].Title)
                #portal_msg += '%s' % active_inspection_brains[0].Title
                ci_brain_zero = active_inspection_brains[0]
                ci_brain_zero_obj = ci_brain_zero.getObject()
                ci_brain_zero_parent = ci_brain_zero_obj.aq_parent
                #portal_msg += '%s' % current_inspection_brains[0].Title
                portal_msg += '%s' % ci_brain_zero_parent.title

                for ci_brain in active_inspection_brains[1:]:
                    #portal_msg += ', <a href="%s">%s</a>' % (ci_brain.getURL(), ci_brain.Title)
                    ci_brain_obj = ci_brain.getObject()
                    ci_brain_parent = ci_brain_obj.aq_parent
                    portal_msg += ', %s' % ci_brain_parent.title

            if guard:
                api.portal.show_message(message=portal_msg,
                                        request=context.REQUEST,
                                        type='info')
            else:
                if len(current_inspection_brains) == 1:
                    last_brain = current_inspection_brains[0]
                    last_brain_obj = last_brain.getObject()
                    lbo_state = api.content.get_state(obj=last_brain_obj)
                    if lbo_state in ['passed', 'failed_final']:
                        return True
            return False

        return True

    def emailInspectors(self):
        """
        There are a minimum of three teams.
        :return:
        """
        context = self
        start_date = getattr(context, 'start_date')
        end_date = getattr(context, 'end_date')

        team_members_dict = {'group_a_member_one' : getattr(self, 'group_a_member_one', None),
                             'group_a_member_two' : getattr(self, 'group_a_member_two', None),
                             'group_b_member_one' : getattr(self, 'group_b_member_one', None),
                             'group_b_member_two' : getattr(self, 'group_b_member_two', None),
                             'group_c_member_one' : getattr(self, 'group_c_member_one', None),
                             'group_c_member_two' : getattr(self, 'group_c_member_two', None),
                             'group_d_member_one' : getattr(self, 'group_d_member_one', None),}

        for team_id in ['group_a', 'group_b', 'group_c', 'group_d',]:
            member_one = team_members_dict.get('%s_member_one' % team_id)
            member_one_fullname = ''
            member_one_email = ''
            if member_one:
                member_obj_one = api.user.get(userid=member_one)
                member_one_fullname = member_obj_one.getProperty('fullname')
                member_one_email = member_obj_one.getProperty('email')
            member_two_fullname = ''
            member_two_email = ''

            member_two = team_members_dict.get('%s_member_two' % team_id)
            if member_two:
                member_obj_two = api.user.get(userid=member_two)
                member_two_fullname = member_obj_two.getProperty('fullname')
                member_two_email = member_obj_two.getProperty('email')

            if member_one and member_two:
                for message_params in [(member_one_fullname, member_one_email, member_two_fullname, member_two_email),
                                (member_two_fullname, member_two_email, member_one_fullname, member_one_email)]:
                    msg = "Dear %s,\n\n" % message_params[2]
                    msg += "Thanks for volunteering to help with The Meadows Annual Property Inspection. You've been paired"
                    msg += " with %s <%s>." % (message_params[0],
                                               message_params[1])
                    msg += " The Inspection begins %s and needs to be completed by %s." % (start_date.strftime('%B %d, %Y'),
                                                                                           end_date.strftime('%B %d, %Y'))
                    msg += "You'll receive more information shortly from the Inspection manager.\n\nThanks - " \
                           "The Meadows Inspection Team."

                    api.portal.send_email(recipient=message_params[3],
                                          subject='The %s Meadows Annual Property Inspection' % start_date.strftime('%Y'),
                                          body=msg)
            elif member_one:
                msg = "Dear %s,\n\n" % member_one_fullname
                msg += "Thanks for volunteering to help with The Meadows Annual Property Inspection."
                msg += " The Inspection begins %s and needs to be completed by %s." % (start_date.strftime('%B %d, %Y'),
                                                                                       end_date.strftime('%B %d, %Y'))
                msg += "You'll receive more information shortly from the Inspection manager.\n\nThanks - " \
                       "The Meadows Inspection Team."

                api.portal.send_email(recipient=member_one_email,
                                      subject='The %s Meadows Annual Property Inspection' % start_date.strftime('%Y'),
                                      body=msg)
            elif member_two:
                msg = "Dear %s,\n\n" % member_two_fullname
                msg += "Thanks for volunteering to help with The Meadows Annual Property Inspection."
                msg += " The Inspection begins %s and needs to be completed by %s." % (start_date.strftime('%B %d, %Y'),
                                                                                       end_date.strftime('%B %d, %Y'))
                msg += "You'll receive more information shortly from the Inspection manager.\n\nThanks - " \
                       "The Meadows Inspection Team."

                api.portal.send_email(recipient=member_two_email,
                                      subject='The %s Meadows Annual Property Inspection' % start_date.strftime('%Y'),
                                      body=msg)

    def createCSVFiles(self, rewalk=False):
        portal = api.portal.get()
        context = self
        house_inspection_title = getattr(self, 'house_inspection_title', None)
        if not house_inspection_title:
            api.portal.show_message(message="We cannot locate the appropriate home inspections. Please verify this "
                                            "inspection was properly configured.",
                                    request=context.REQUEST,
                                    type='warning')
            return

        current_state = 'failed_initial'
        if rewalk:
            current_state = 'failed_final'

        neighborhood_container = context.aq_parent
        neighborhood_path = '/'.join(neighborhood_container.getPhysicalPath())
        #get all house passed inspections
        passed_inspection_brains = context.portal_catalog.searchResults(
            path={'query': neighborhood_path, 'depth': 3},
            object_provides=IHOAHouseInspection.__identifier__,
            review_state='passed')

        failed_inspection_brains = context.portal_catalog.searchResults(
            path={'query': neighborhood_path, 'depth': 3},
            object_provides=IHOAHouseInspection.__identifier__,
            review_state=current_state)

        failure_csv_headers = ['Full_Name',
                             'Address1',
                             'Address2',
                             'divlot',
                             'City',
                             'State',
                             'Zip',
                             'toda_date',
                             'finding_1',
                             'remediation_date_1',
                             'finding_2',
                             'remediation_date_2',
                             'finding_3',
                             'remediation_date_3']
        passing_csv_headers = ['Full_Name',
                             'Address1',
                             'Address2',
                             'divlot',
                             'City',
                             'State',
                             'Zip',
                             'toda_date']

        passing_csv_dicts = []
        failure_csv_dicts = []

        today = date.today()
        todays_date = today.strftime('%B %d, %Y')
        today_timestamp = today.strftime('%Y_%b_%d')

        house_pass_log = getattr(context, 'csv_pass_log')
        if house_pass_log is None:
            house_pass_log = {}

        previously_passed_houses = house_pass_log.keys()

        working_house_pass_log_dict = {}
        working_house_fail_log_dict = {}

        for pi_brain in passed_inspection_brains:
            pi_brain_id = pi_brain.getId
            if pi_brain_id != house_inspection_title:
                continue
            pi_obj = pi_brain.getObject()
            pi_home_obj = pi_obj.aq_parent
            pi_home_obj_id = pi_home_obj.id
            if pi_home_obj_id in previously_passed_houses:
                continue

            people_to_mail = []
            for to_notify in ['owner_one', 'owner_two', 'property_manager']:
                ptn = getattr(pi_home_obj, to_notify, None)
                if ptn:
                    people_to_mail.append(ptn)

            working_house_pass_log_dict.update({pi_home_obj_id:people_to_mail})

            street_number = getattr(pi_home_obj, 'street_number', '')
            street_address = getattr(pi_home_obj, 'street_address', '')
            city = getattr(pi_home_obj, 'city', '')
            state = getattr(pi_home_obj, 'state', '')
            zipcode = getattr(pi_home_obj, 'zipcode', '')
            div = getattr(pi_home_obj, 'div', '')
            lot = getattr(pi_home_obj, 'lot', '')
            div_lot = "%s_%s" % (div, lot)
            address_string1 = "%s %s" % (street_number,
                                         street_address,)
            address_string2 = ""

            for ptn in people_to_mail:
                member_data = api.user.get(userid=ptn)
                member_fullname = member_data.getProperty('fullname')
                use_meadows_address = member_data.getProperty('use_local_address')
                if not use_meadows_address:
                    remote_address1 = member_data.getProperty('mailing_address_1')
                    if remote_address1:
                        passing_csv_dicts.append({'Full_Name':member_fullname,
                                              'Address1':remote_address1,
                                              'Address2':member_data.getProperty('mailing_address_2'),
                                              'divlot':div_lot,
                                              'City':member_data.getProperty('mailing_city'),
                                              'State':member_data.getProperty('mailing_state'),
                                              'Zip':member_data.getProperty('mailing_zipcode'),
                                              'toda_date':todays_date})
                        continue

                passing_csv_dicts.append({'Full_Name':member_fullname,
                                          'Address1':address_string1,
                                          'Address2':address_string2,
                                          'divlot':div_lot,
                                          'City':city,
                                          'State':state,
                                          'Zip':zipcode,
                                          'toda_date':todays_date})

        setattr(context, 'csv_pass_log', working_house_pass_log_dict)

        for fi_brain in failed_inspection_brains:
            fi_brain_id = fi_brain.getId
            if fi_brain_id != house_inspection_title:
                continue
            fi_obj = fi_brain.getObject()
            fi_home_obj = fi_obj.aq_parent
            fi_home_obj_id = fi_home_obj.id

            street_number = getattr(fi_home_obj, 'street_number', '')
            street_address = getattr(fi_home_obj, 'street_address', '')
            city = getattr(fi_home_obj, 'city', '')
            state = getattr(fi_home_obj, 'state', '')
            zipcode = getattr(fi_home_obj, 'zipcode', '')
            div = getattr(fi_home_obj, 'div', '')
            lot = getattr(fi_home_obj, 'lot', '')
            div_lot = "%s_%s" % (div, lot)
            address_string1 = "%s %s" % (street_number,
                                        street_address,)
            address_string2 = ""

            fpeople_to_mail = []
            for to_notify in ['owner_one', 'owner_two', 'property_manager']:
                ptn = getattr(fi_home_obj, to_notify, None)
                if ptn:
                    fpeople_to_mail.append(ptn)


            fieldsets = IHOAHOUSEINSPECTION_FIELDSETS
            failure_dicts = []
            for fieldset in fieldsets:
                action_required = getattr(fi_obj, '%s_action_required' % fieldset, '')
                cond_remains = getattr(fi_obj, '%s_cond_remains' % fieldset, '')
                if rewalk:
                    if action_required and cond_remains:
                        text = getattr(fi_obj, '%s_text' % fieldset, '')
                        rewalk_text = getattr(fi_obj, '%s_rewalk_text' % fieldset, '')
                        #cond_remains = getattr(fi_obj, '%s_cond_remains' % fieldset, '')
                        f_dict = {'fieldset':fieldset,
                                  'action_required':action_required,
                                  'text':text,
                                  'rewalk_text':rewalk_text,
                                  'cond_remains':cond_remains
                                  }
                        failure_dicts.append(f_dict)
                else:
                    if action_required:
                        text = getattr(fi_obj, '%s_text' % fieldset, '')
                        rewalk_text = getattr(fi_obj, '%s_rewalk_text' % fieldset, '')
                        #cond_remains = getattr(fi_obj, '%s_cond_remains' % fieldset, '')
                        f_dict = {'fieldset':fieldset,
                                  'action_required':action_required,
                                  'text':text,
                                  'rewalk_text':rewalk_text,
                                  'cond_remains':cond_remains
                                  }
                        failure_dicts.append(f_dict)
            #failure_dict_keys = failure_dicts.keys()

            finding_one_text = 'None'
            finding_one_date = 'None'
            finding_two_text = 'None'
            finding_two_date = 'None'
            finding_three_text = 'None'
            finding_three_date = 'None'

            if len(failure_dicts) >= 3:
                failure_one_dict = failure_dicts[0]
                failure_two_dict = failure_dicts[1]
                failure_three_dict = failure_dicts[2]
                if rewalk:
                    fieldset_one_id = failure_one_dict.get('fieldset')
                    fieldset_one_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_one_id)
                    finding_one_text = '%s: %s' % (fieldset_one_title, failure_one_dict.get('rewalk_text'))
                    finding_one_date = 'Immediate.'

                    fieldset_two_id = failure_two_dict.get('fieldset')
                    fieldset_two_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_two_id)
                    finding_two_text = '%s: %s' % (fieldset_two_title, failure_two_dict.get('rewalk_text'))
                    finding_two_date = 'Immediate.'

                    fieldset_three_id = failure_two_dict.get('fieldset')
                    fieldset_three_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_three_id)
                    finding_three_text = '%s: %s' % (fieldset_three_title, failure_three_dict.get('rewalk_text'))
                    finding_three_date = 'Immediate.'
                else:
                    fieldset_one_id = failure_one_dict.get('fieldset')
                    fieldset_one_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_one_id)
                    finding_one_text = '%s: %s' % (fieldset_one_title, failure_one_dict.get('text'))
                    fieldset_key = failure_one_dict.get('fieldset')
                    action_required_key = failure_one_dict.get('action_required')
                    action_required_dict = REQUIRED_ACTION_DICT.get(fieldset_key)
                    finding_one_date = action_required_dict.get(action_required_key)

                    fieldset_two_id = failure_two_dict.get('fieldset')
                    fieldset_two_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_two_id)
                    finding_two_text = '%s: %s' % (fieldset_two_title, failure_two_dict.get('text'))
                    f2_fieldset_key = failure_two_dict.get('fieldset')
                    f2_action_required_key = failure_two_dict.get('action_required')
                    f2_action_required_dict = REQUIRED_ACTION_DICT.get(f2_fieldset_key)
                    finding_two_date = f2_action_required_dict.get(f2_action_required_key)

                    fieldset_three_id = failure_three_dict.get('fieldset')
                    fieldset_three_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_three_id)
                    finding_three_text = '%s: %s' % (fieldset_three_title, failure_three_dict.get('text'))
                    f3_fieldset_key = failure_three_dict.get('fieldset')
                    f3_action_required_key = failure_three_dict.get('action_required')
                    f3_action_required_dict = REQUIRED_ACTION_DICT.get(f3_fieldset_key)
                    finding_three_date = f3_action_required_dict.get(f3_action_required_key)

            elif len(failure_dicts) == 2:
                failure_one_dict = failure_dicts[0]
                failure_two_dict = failure_dicts[1]
                if rewalk:
                    fieldset_one_id = failure_one_dict.get('fieldset')
                    fieldset_one_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_one_id)
                    finding_one_text = '%s: %s' % (fieldset_one_title, failure_one_dict.get('rewalk_text'))
                    finding_one_date = 'Immediate.'
                    fieldset_two_id = failure_two_dict.get('fieldset')
                    fieldset_two_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_two_id)
                    finding_two_text = '%s: %s' % (fieldset_two_title, failure_two_dict.get('rewalk_text'))
                    finding_two_date = 'Immediate.'
                else:
                    fieldset_one_id = failure_one_dict.get('fieldset')
                    fieldset_one_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_one_id)
                    finding_one_text = '%s: %s' % (fieldset_one_title, failure_one_dict.get('text'))
                    fieldset_key = failure_one_dict.get('fieldset')
                    action_required_key = failure_one_dict.get('action_required')
                    action_required_dict = REQUIRED_ACTION_DICT.get(fieldset_key)
                    finding_one_date = action_required_dict.get(action_required_key)

                    fieldset_two_id = failure_two_dict.get('fieldset')
                    fieldset_two_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_two_id)
                    finding_two_text = '%s: %s' % (fieldset_two_title, failure_two_dict.get('text'))
                    f2_fieldset_key = failure_two_dict.get('fieldset')
                    f2_action_required_key = failure_two_dict.get('action_required')
                    f2_action_required_dict = REQUIRED_ACTION_DICT.get(f2_fieldset_key)
                    finding_two_date = f2_action_required_dict.get(f2_action_required_key)

            elif len(failure_dicts) == 1:
                failure_one_dict = failure_dicts[0]

                fieldset_id = failure_one_dict.get('fieldset')
                fieldset_title = IHOAHOUSEINSPECTION_FIELDSET_TITLES_DICT.get(fieldset_id)
                finding_one_text = '%s: %s' % (fieldset_title, failure_one_dict.get('text'))
                fieldset_key = failure_one_dict.get('fieldset')
                action_required_key = failure_one_dict.get('action_required')
                action_required_dict = REQUIRED_ACTION_DICT.get(fieldset_key)
                finding_one_date = action_required_dict.get(action_required_key)


            for ptn in fpeople_to_mail:
                member_data = api.user.get(userid=ptn)
                member_fullname = member_data.getProperty('fullname')
                use_meadows_address = member_data.getProperty('use_local_address')
                if not use_meadows_address:
                    remote_address1 = member_data.getProperty('mailing_address_1')
                    if remote_address1:
                        failure_csv_dicts.append({'Full_Name':member_fullname,
                                                  'Address1':remote_address1,
                                                  'Address2':member_data.getProperty('mailing_address_2'),
                                                  'divlot':div_lot,
                                                  'City':member_data.getProperty('mailing_city'),
                                                  'State':member_data.getProperty('mailing_state'),
                                                  'Zip':member_data.getProperty('mailing_zipcode'),
                                                  'toda_date':todays_date,
                                                  'finding_1': finding_one_text,
                                                  'remediation_date_1': finding_one_date,
                                                  'finding_2': finding_two_text,
                                                  'remediation_date_2': finding_two_date,
                                                  'finding_3': finding_three_text,
                                                  'remediation_date_3': finding_three_date})
                        continue

                failure_csv_dicts.append({'Full_Name': member_fullname,
                                       'Address1': address_string1,
                                       'Address2': address_string2,
                                       'divlot': div_lot,
                                       'City': city,
                                       'State': state,
                                       'Zip': zipcode,
                                       'toda_date': todays_date,
                                       'finding_1': finding_one_text,
                                       'remediation_date_1': finding_one_date,
                                       'finding_2': finding_two_text,
                                       'remediation_date_2': finding_two_date,
                                       'finding_3': finding_three_text,
                                       'remediation_date_3': finding_three_date})

        inspection_state = 'initial'
        if rewalk:
            inspection_state = 'rewalk'

        passing_file_id = '%s_%s_inspection_passing.csv' % (today_timestamp, inspection_state)
        passing_file_title = '%s %s Inspection Passing CSV' % (todays_date, inspection_state)
        failing_file_id = '%s_%s_inspection_failures.csv' % (today_timestamp, inspection_state)
        failing_file_title = '%s %s Inspection Failures CSV' % (todays_date, inspection_state)



        passing_file = ''
        p_buffer = StringIO()
        p_writer = csv.DictWriter(p_buffer, fieldnames=passing_csv_headers, delimiter=',', quoting=csv.QUOTE_ALL)
        p_writer.writeheader()
        for p_dict in passing_csv_dicts:
            p_writer.writerow(p_dict)

        p_value = p_buffer.getvalue()
        p_value = unicode(p_value, 'utf-8').encode("iso-8859-1", "replace")

        failing_file = ''
        f_buffer = StringIO()
        f_writer = csv.DictWriter(f_buffer, fieldnames=failure_csv_headers, delimiter=',', quoting=csv.QUOTE_ALL)
        f_writer.writeheader()
        for f_dict in failure_csv_dicts:
            f_writer.writerow(f_dict)

        f_value = f_buffer.getvalue()
        f_value = unicode(f_value, 'utf-8').encode("iso-8859-1", "replace")

        logger.info('creating files in %s' % context.id)
        #import pdb;pdb.set_trace()

        pass_csv = api.content.create(type='File',
                                      id=passing_file_id,
                                      title=passing_file_title.title(),
                                      container=context
                                      )

        fail_csv = api.content.create(type='File',
                                      id=failing_file_id,
                                      title=failing_file_title.title(),
                                      container=context
                                      )

        setattr(pass_csv, 'file', NamedBlobFile(data=p_value,
                                              filename=unicode(passing_file_id)))

        setattr(fail_csv, 'file', NamedBlobFile(data=f_value,
                                                filename=unicode(failing_file_id)))
        #import pdb;pdb.set_trace()
        # context.invokeFactory('File',
        #                       id=passing_file_id,
        #                       title=passing_file_title.title(),
        #                       content_type='text/csv',
        #                       file=p_value)
        #
        # context.invokeFactory('File',
        #                       id=failing_file_id,
        #                       title=failing_file_title.title(),
        #                       content_type='text/csv',
        #                       file=f_value)
        # pass_csv = context[passing_file_id]
        # fail_csv = context[failing_file_id]
        #
        pass_csv.setFormat('text/csv')
        fail_csv.setFormat('text/csv')


    def sendEmailNotices(self, rewalk=False):
        portal = api.portal.get()
        context = self
        house_inspection_title = getattr(self, 'house_inspection_title', None)
        if not house_inspection_title:
            api.portal.show_message(message="We cannot locate the appropriate home inspections. Please verify this "
                                            "inspection was properly configured.",
                                    request=context.REQUEST,
                                    type='warning')
            return

        current_state = 'failed_initial'
        if rewalk:
            current_state = 'failed_final'

        neighborhood_container = context.aq_parent
        neighborhood_path = '/'.join(neighborhood_container.getPhysicalPath())
        #get all house passed inspections
        passed_inspection_brains = context.portal_catalog.searchResults(
            path={'query': neighborhood_path, 'depth': 3},
            object_provides=IHOAHouseInspection.__identifier__,
            review_state='passed')

        failed_inspection_brains = context.portal_catalog.searchResults(
            path={'query': neighborhood_path, 'depth': 3},
            object_provides=IHOAHouseInspection.__identifier__,
            review_state=current_state)

        inspection_passed_message = getattr(neighborhood_container, 'initial_pass_message', u'')
        inspection_failure_message = getattr(neighborhood_container, 'initial_fail_message', u'')
        if rewalk:
            inspection_passed_message = getattr(neighborhood_container, 'rewalk_pass_message', u'')
            inspection_failure_message = getattr(neighborhood_container, 'rewalk_fail_message', u'')

        if not inspection_failure_message:
            inspection_failure_message = u""

        if not inspection_passed_message:
            inspection_passed_message = u""

        house_pass_log = getattr(context, 'house_pass_log')
        if house_pass_log is None:
            house_pass_log = {}

        previously_passed_houses = house_pass_log.keys()

        working_house_pass_log_dict = {}
        working_house_fail_log_dict = {}

        secretary_email = getattr(neighborhood_container, 'secretary_email', None)
        pass_message_subject = "Your property has passed The Meadows Annual Inspection"
        fail_message_subject = "Meadows Property Inspection - Your property has failed the inspection"
        if rewalk:
            fail_message_subject = "Meadows Property Inspection - Your property has failed The Meadows re-inspection."

        for pi_brain in passed_inspection_brains:
            pi_brain_id = pi_brain.getId
            if pi_brain_id != house_inspection_title:
                continue
            pi_obj = pi_brain.getObject()
            pi_home_obj = pi_obj.aq_parent
            pi_home_obj_id = pi_home_obj.id
            if pi_home_obj_id in previously_passed_houses:
                continue

            people_to_email = []
            for to_notify in ['owner_one', 'owner_two', 'property_manager']:
                ptn = getattr(pi_home_obj, to_notify, None)
                if ptn:
                    people_to_email.append(ptn)

            working_house_pass_log_dict.update({pi_home_obj_id:people_to_email})

            street_number = getattr(pi_home_obj, 'street_number', '')
            street_address = getattr(pi_home_obj, 'street_address', '')
            # city = getattr(pi_home_obj, 'city', '')
            # state = getattr(pi_home_obj, 'state', '')
            # zipcode = getattr(pi_home_obj, 'zipcode', '')
            address_string = "%s %s" % (street_number,
                                        street_address,)
            for ptn in people_to_email:
                member_data = api.user.get(userid=ptn)
                member_fullname = member_data.getProperty('fullname')
                member_email = member_data.getProperty('email')
                pass_message = "Dear %s,\n\n" % member_fullname
                html_pass_msg = "<p>Dear %s,</p>" % member_fullname

                if rewalk:
                    pass_message += "Your home at: %s Passed the Second Inspection of The Meadows Annual Property " \
                                    "Inspection.\n\n" % address_string
                    html_pass_msg += "<p>Your home at: %s Passed the Second Inspection of The Meadows Annual Property " \
                                     "Inspection.</p>" % address_string
                else:
                    pass_message += "Your home at: %s Passed The Meadows Annual Property Inspection.\n\n" % address_string
                    html_pass_msg += "<p>Your home at: %s Passed The Meadows Annual Property Inspection.</p>" % address_string

                pass_message += "You have no further action.\n\n"
                html_pass_msg += "<p>You have no further action.</p>"

                pass_message += "The Meadows community prides itself in maintaining our community appearance to " \
                                "benefit all residents. We appreciate your help.\n\n"
                html_pass_msg += "<p>The Meadows community prides itself in maintaining our community appearance to " \
                                 "benefit all residents. We appreciate your help.</p>"

                pass_message += "\n\nRegards,\n\nThe Meadows Board"
                html_pass_msg += "<p>Regards,<br /><br />The Meadows Board</p>"

                pass_msg = MIMEMultipart('related')
                pass_msg_alt = MIMEMultipart('alternative')

                pass_msg['Subject'] = "Your property has passed The Meadows Annual Inspection"
                pass_msg['From'] = secretary_email
                pass_msg['To'] = member_email
                pass_msg.preamble = 'This is a multi-part message in MIME format.'
                pass_msg.attach(pass_msg_alt)

                meadows_logo = portal.restrictedTraverse("++resource++docent.hoa.houses/theMeadows.jpeg")
                if meadows_logo:
                    msg_image = MIMEImage(meadows_logo.GET())
                    msg_image.add_header('Content-ID', '<meadows_logo>')
                    pass_msg.attach(msg_image)

                send_message_html = "<html><body><div><div style='width: 100%%; height: 88px;'><div style='float:right'><img src='cid:meadows_logo'></div></div><div>"
                send_message = pass_message
                send_message_html += html_pass_msg
                send_message_html += "</div></div></body></html>"

                pass_msg_alt.attach(MIMEText(send_message, 'plain'))
                pass_msg_alt.attach(MIMEText(send_message_html, 'html'))

                host = portal.MailHost
                host.send(pass_msg, immediate=True)

        for fi_brain in failed_inspection_brains:
            fi_brain_id = fi_brain.getId
            if fi_brain_id != house_inspection_title:
                continue
            fi_obj = fi_brain.getObject()
            fi_home_obj = fi_obj.aq_parent
            fi_home_obj_id = fi_home_obj.id

            people_to_email = []
            for to_notify in ['owner_one', 'owner_two', 'property_manager']:
                ptn = getattr(fi_home_obj, to_notify, None)
                if ptn:
                    people_to_email.append(ptn)

            working_house_fail_log_dict.update({fi_home_obj_id:people_to_email})
            street_number = getattr(fi_home_obj, 'street_number', '')
            street_address = getattr(fi_home_obj, 'street_address', '')
            city = getattr(fi_home_obj, 'city', '')
            state = getattr(fi_home_obj, 'state', '')
            zipcode = getattr(fi_home_obj, 'zipcode', '')
            div = getattr(fi_home_obj, 'div', '')
            lot = getattr(fi_home_obj, 'lot', '')
            inspection_type = 'Initial Inspection'
            if rewalk:
                inspection_type = 'Final Inspection'

            address_string = "%s %s" % (street_number,
                                        street_address)

            fieldsets = IHOAHOUSEINSPECTION_FIELDSETS
            failure_dicts = []
            for fieldset in fieldsets:
                action_required = getattr(fi_obj, '%s_action_required' % fieldset, '')
                if action_required:
                    text = getattr(fi_obj, '%s_text' % fieldset, '')
                    rewalk_text = getattr(fi_obj, '%s_rewalk_text' % fieldset, '')
                    cond_remains = getattr(fi_obj, '%s_cond_remains' % fieldset, '')
                    image = getattr(fi_obj, '%s_image' % fieldset, None)
                    rewalk_image = getattr(fi_obj, '%s_rewalk_image' % fieldset, None)
                    f_dict = {'fieldset':fieldset,
                              'action_required':action_required,
                              'text':text,
                              'rewalk_text':rewalk_text,
                              'cond_remains':cond_remains,
                              'image':image,
                              'rewalk_image':rewalk_image
                              }
                    failure_dicts.append(f_dict)

            images_to_attach = []

            fail_message = ""
            fail_html = ""
            if rewalk:
                fail_message += "Your home at: %s, (Division %s Lot %s) Failed Second Inspection of The Meadows Annual " \
                                "Property Inspection. " % (address_string, div, lot)
                fail_message += "Because this is the second failure for the same violation(s), in accordance with our " \
                                "rules, you are being fined $100. You will receive a fine notification from our " \
                                "property manager."
                fail_html += "<p>Your home at: %s (Division %s Lot %s) " % (address_string, div, lot)
                fail_html += "<span style='color:red;'>Failed</span> the <em>Second Inspection</em> ofThe Meadows " \
                             "Annual Property Inspection. <em>Because this is the second failure for the same violation(s), " \
                             "in accordance with our rules, you are being fined $100. You will receive a fine " \
                             "notification from our property manager.</em></p><hr width='80%'>"
            else:
                fail_message += "Your home at: %s, (Division %s Lot %s) Failed The Meadows Annual Property Inspection " \
                                "completed this week:\n\n" % (address_string, div, lot)
                fail_html += "<p>Your home at: %s (Division %s Lot %s) " % (address_string, div, lot)
                fail_html += "<span style='color:red;'>Failed</span> The Meadows Annual Property Inspection completed " \
                             "this week.</p><hr width='80%'>"
            for failure_dict in failure_dicts:
                if rewalk:
                    condition_remains = failure_dict.get('cond_remains')
                    if not condition_remains:
                        continue
                fail_message += '%s\n' % failure_dict.get('fieldset').title()
                fail_html += "<h4>%s</h4><ul style='list-style-type: none;'>" % failure_dict.get('fieldset').title()

                fieldset_key = failure_dict.get('fieldset')
                action_required_key = failure_dict.get('action_required')
                action_required_dict = REQUIRED_ACTION_DICT.get(fieldset_key)
                action_required = action_required_dict.get(action_required_key)

                year_str = date.today().strftime('%Y')
                action_required_str = '%s, %s' % (action_required, year_str)
                if action_required_key == 'replace':
                    year_str = str(int(year_str)+1)
                    action_required_str = '%s %s' % (action_required, year_str)

                if rewalk:
                    fail_message += "Failed for: %s\n" % failure_dict.get('rewalk_text')
                    fail_html += "<li>Failed for: %s</li>" % failure_dict.get('rewalk_text')

                    # fail_message += "Remediation Date: %s\n\n" % action_required_str
                    # fail_html += "<li>Remediation Date: %s</li>" % action_required_str
                    rewalk_image = failure_dict.get('rewalk_image')
                    if rewalk_image:
                        rewalk_image_id = '%s_rewalk_image' % fieldset_key
                        msg_image = MIMEImage(rewalk_image.data)
                        msg_image.add_header('Content-ID', '<%s>' % rewalk_image_id)
                        images_to_attach.append(msg_image)
                        fail_html += "<li><img src='cid:%s' height='150' width='200'></li>" % rewalk_image_id
                else:
                    fail_message += "Failed for: %s\n" % failure_dict.get('text')
                    fail_html += "<li>Failed for: %s</li>" % failure_dict.get('text')

                    fail_message += "Remediation Date: %s\n\n" % action_required_str
                    fail_html += "<li>Remediation Date: %s</li>" % action_required_str
                    image = failure_dict.get('image')
                    if image:
                        image_id = '%s_image' % fieldset_key
                        msg_image = MIMEImage(image.data)
                        msg_image.add_header('Content-ID', '<%s>' % image_id)
                        images_to_attach.append(msg_image)
                        fail_html += "<li><img src='cid:%s' height='150' width='200'></li>" % image_id

                fail_html += '</ul>'


            fail_html += "<hr width='80%'>"

            #fail_message += inspection_failure_message
            #fail_html += "<p>%s</p>" % inspection_failure_message

            if not rewalk:
                fail_message += "Please note this was the %s. The Association will re-inspect your property on or " \
                                "after remediation date shown above, and will levy a fine against your unit unless " \
                                "you remediate the above findings.\n\n" % inspection_type
                fail_html += "<p>Please note this was the <em>%s</em>. The Association will re-inspect your property on or " \
                                "after remediation date shown above, and will levy a fine against your unit unless " \
                                "you remediate the above findings.</p>" % inspection_type

            if not rewalk:
                fail_message += "Actions You May Take Before compliance date:\n\n    1. Fix the items before the " \
                                "remediation date above.\n"
                fail_html += "<p>Actions You May Take Before compliance date:</p>" \
                             "<ul style='list-style-type: decimal;'>"
                fail_html += "<li>Fix the items before the remediation date above.</li>"
            else:
                fail_message += "Actions You May Take:\n\n    1. Fix the discrepancies as soon as possible and notify " \
                                "the board. Note: Monthly fines will accrue until you complete the work, notify " \
                                "the board, and the board re-inspects and is satisfied with the work."

                fail_html += "<p>Actions You May Take</p>" \
                             "<ul style='list-style-type: decimal;'>"
                fail_html += "<li>Fix the discrepancies as soon as possible and notify the board. Note: Monthly " \
                             "fines will accrue until you complete the work, notify the board, and the board " \
                             "re-inspects and is satisfied with the work.</li>"

            fail_message += "    2. Contact the board at " \
                            "property-inspection@themeadowsofredmond.org with questions or to request more time. " \
                            "The board believes existing rules provided adequate time; therefore, there needs to " \
                            "be a specific reason and schedule for any extension.\n    3. Contest these finding " \
                            "within 15 days by emailing the board at property-inspection@themeadowsofredmond.org " \
                            "and/or attending the next board meeting (provided it is within 15 days of this " \
                            "letter). Please be specific with your disagreement.\n\n"

            fail_html += "<li>Contact the board at <a href='mailto:property-inspection@themeadowsofredmond.org'>" \
                         "property-inspection@themeadowsofredmond.org</a> with questions or to request more time. " \
                         "The board believes existing rules provided adequate time; therefore, there needs to be " \
                         "a specific reason and schedule for any extension.</li>"
            fail_html += "<li>Contest these finding within 15 days by emailing the board at " \
                         "<a href='mailto:property-inspection@themeadowsofredmond.org'>property-inspection@" \
                         "themeadowsofredmond.org</a> and/or attending the next board meeting " \
                         "(provided it is within 15 days of this letter). Please be specific with your " \
                         "disagreement.</li>"
            fail_html += "</ul>"

            if rewalk:
                fail_message += "Fines accrued for weedwalk violations are treated as any debt to the Association and " \
                                "all debt collection actions provided by our debt collection policy will be enforced. " \
                                "Thank you very much for your cooperation.\n\n"
                fail_html += "<p>Fines accrued for weedwalk violations are treated as any debt to the Association and " \
                             "all debt collection actions provided by our debt collection policy will be enforced. " \
                             "Thank you very much for your cooperation.</p>"

            fail_message += "\n\nThanks,\n\nThe Meadows Board"
            fail_html += "<p>Thanks,<br /><br />The Meadows Board</p>"

            for ptn in people_to_email:
                member_data = api.user.get(userid=ptn)
                member_fullname = member_data.getProperty('fullname')
                member_email = member_data.getProperty('email')
                msg = MIMEMultipart('related')
                msg_alt = MIMEMultipart('alternative')

                msg['Subject'] = fail_message_subject
                msg['From'] = secretary_email
                msg['To'] = member_email
                msg.preamble = 'This is a multi-part message in MIME format.'
                msg.attach(msg_alt)

                for i_t_a in images_to_attach:
                    msg.attach(i_t_a)

                meadows_logo = portal.restrictedTraverse("++resource++docent.hoa.houses/theMeadows.jpeg")
                if meadows_logo:
                    msg_image = MIMEImage(meadows_logo.GET())
                    msg_image.add_header('Content-ID', '<meadows_logo>')
                    msg.attach(msg_image)

                send_message = "Dear %s,\n\n" % member_fullname
                send_message_html = "<html><body><div><div style='width: 100%%; height: 88px;'><div style='float:right'><img src='cid:meadows_logo'></div></div>" \
                                    "<div><p>Dear %s,</p>" % member_fullname
                send_message += fail_message
                send_message_html += fail_html
                send_message_html += "</div></div></body></html>"

                msg_alt.attach(MIMEText(send_message, 'plain'))
                msg_alt.attach(MIMEText(send_message_html, 'html'))

                host = portal.MailHost
                host.send(msg, immediate=True)

        if rewalk:
            setattr(context, 'rewalk_pass_log', working_house_pass_log_dict)
            setattr(context, 'rewalk_failure_log', working_house_fail_log_dict)
        else:
            setattr(context, 'house_pass_log', working_house_pass_log_dict)
            setattr(context, 'house_failure_log', working_house_fail_log_dict)

