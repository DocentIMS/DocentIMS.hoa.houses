import logging
from datetime import date

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
from docent.hoa.houses.app_config import HOME_ROLE_TO_ATTRIBUTE_LOOKUP_DICT, LOT_DIVISION_DICT, WALKERS_GROUP_IDS
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

    form.mode(rewalk_failure_log='hidden')
    rewalk_failure_log = schema.Dict(
        title=_(u'Homes Sent Rewalk Pass Notices'),
        description=_(u"Emails sent to the following home owners."),
        key_type=schema.ASCIILine(),
        value_type=schema.List(value_type=schema.ASCIILine()),
        required=False,
    )

    form.mode(rewalk_pass_log='hidden')
    rewalk_pass_log = schema.Dict(
        title=_(u'Homes Sent Rewalk Pass Notices'),
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

    fieldset('team_e',
        label=u'Team E',
        description=u'',
        fields=['group_e_member_one',
                'group_e_member_two', ]
    )

    group_e_member_one = schema.Choice(
        title=_(u"Group E Member One"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    group_e_member_two = schema.Choice(
        title=_(u"Group E Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
        default='',
    )

    # @invariant
    # def minimumThreeGroups(data):
    #     assigned_members = 0
    #     team_a = 0
    #     team_b = 0
    #     team_c = 0
    #     team_d = 0
    #     team_e = 0
    #     group_a_member_one = getattr(data, 'group_a_member_one', None)
    #     if group_a_member_one:
    #         assigned_members += 1
    #         team_a += 1
    #     group_a_member_two = getattr(data, 'group_a_member_two', None)
    #     if group_a_member_two:
    #         assigned_members += 1
    #         team_a += 1
    #     group_b_member_one = getattr(data, 'group_b_member_one', None)
    #     if group_b_member_one:
    #         assigned_members += 1
    #         team_b += 1
    #     group_b_member_two = getattr(data, 'group_b_member_two', None)
    #     if group_b_member_two:
    #         assigned_members += 1
    #         team_b += 1
    #     group_c_member_one = getattr(data, 'group_c_member_one', None)
    #     if group_c_member_one:
    #         assigned_members += 1
    #         team_c += 1
    #     group_c_member_two = getattr(data, 'group_c_member_two', None)
    #     if group_c_member_two:
    #         assigned_members += 1
    #         team_c += 1
    #     group_d_member_one = getattr(data, 'group_d_member_one', None)
    #     if group_d_member_one:
    #         assigned_members += 1
    #         team_d += 1
    #     group_d_member_two = getattr(data, 'group_d_member_two', None)
    #     if group_d_member_two:
    #         assigned_members += 1
    #         team_d += 1
    #     group_e_member_one = getattr(data, 'group_e_member_one', None)
    #     if group_e_member_one:
    #         assigned_members += 1
    #         team_e += 1
    #     group_e_member_two = getattr(data, 'group_e_member_two', None)
    #     if group_e_member_two:
    #         assigned_members += 1
    #         team_e += 1
    #
    #     if not team_a:
    #         raise Invalid(_(u"You must have at least one walker for Team A."))
    #
    #     if not team_b:
    #         raise Invalid(_(u"You must have at least one walker for Team B."))
    #
    #     if not team_c:
    #         raise Invalid(_(u"You must have at least one walker for Team C."))
    #
    #     if group_a_member_one == group_a_member_two:
    #         raise Invalid(_(u"You have the same member listed twice in Team A."))
    #
    #     if group_b_member_one == group_b_member_two:
    #         raise Invalid(_(u"You have the same member listed twice in Team B."))
    #
    #     if group_c_member_one == group_c_member_two:
    #         raise Invalid(_(u"You have the same member listed twice in Team C."))
    #
    #     if team_e and not team_d:
    #         raise Invalid(_(u"Please assign walkers to Team D before Team E."))

    # @invariant
    # def validateGroups(data):
    #     assigned_members = []
    #     for m_id in ['group_a_member_one'
    #                  'group_a_member_two',
    #                  'group_b_member_one',
    #                  'group_b_member_two',
    #                  'group_c_member_one',
    #                  'group_c_member_two',
    #                  'group_d_member_one',
    #                  'group_d_member_two',
    #                  'group_e_member_one',
    #                  'group_e_member_two']:
    #         a_value = getattr(data, m_id, None)
    #         if a_value:
    #             assigned_members.append(a_value)
    #
    #     sorted_dict = Counter(assigned_members)
    #     import pdb;pdb.set_trace()
    #     for k, v in sorted_dict.iteritems():
    #         if v >= 2:
    #             member_data = api.user.get(userid=k)
    #             fullname = member_data.getProperty('fullname')
    #             portal = api.portal.get()
    #             api.portal.show_message(message="%s has been assigned to multiple groups." % fullname,
    #                                     request=portal.REQUEST,
    #                                     type='warning')






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

    def after_transition_processor(self):
        context_state = api.content.get_state(obj=self)
        if context_state == 'initial_inspection':
            self.propagate_house_inspections()
            self.assign_security()

        if context_state == 'secondary_inspection':
            #self.sendEmailNotices()
            logger.info('Emails Sent')

        if context_state == 'closed':
            #self.sendEmailNotices(rewalk=True)
            logger.info('Emails Sent')

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
        group_e_member_one = getattr(self, 'group_e_member_one', None)
        group_e_member_two = getattr(self, 'group_e_member_two', None)

        if group_a_member_one:
            api.group.add_user(groupname='walkers_a', username=group_a_member_one)
        if group_a_member_two:
            api.group.add_user(groupname='walkers_a', username=group_a_member_two)
        if group_b_member_one:
            api.group.add_user(groupname='walkers_b', username=group_b_member_one)
        if group_b_member_two:
            api.group.add_user(groupname='walkers_b', username=group_b_member_two)
        if group_c_member_one:
            api.group.add_user(groupname='walkers_c', username=group_c_member_one)
        if group_c_member_two:
            api.group.add_user(groupname='walkers_c', username=group_c_member_two)
        if group_d_member_one:
            api.group.add_user(groupname='walkers_d', username=group_d_member_one)
        if group_d_member_two:
            api.group.add_user(groupname='walkers_d', username=group_d_member_two)
        if group_e_member_one:
            api.group.add_user(groupname='walkers_e', username=group_e_member_one)
        if group_e_member_two:
            api.group.add_user(groupname='walkers_e', username=group_e_member_two)


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
        group_e_member_one = getattr(self, 'group_e_member_one', None)
        group_e_member_two = getattr(self, 'group_e_member_two', None)

        number_of_groups = 0
        if group_a_member_one or group_a_member_two:
            number_of_groups += 1
        if group_b_member_one or group_b_member_one:
            number_of_groups += 1
        if group_c_member_one or group_c_member_two:
            number_of_groups += 1
        if group_d_member_one or group_d_member_two:
            number_of_groups += 1
        if group_e_member_one or group_e_member_two:
            number_of_groups += 1

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
                setattr(new_insp, 'title', house_obj_title)
                added_inspections += 1

        api.portal.show_message(message=u"%s houses prepared for annual inspection." % added_inspections,
                                request=context.REQUEST,
                                type='info')

    def verifyFirstInspectionComplete(self):
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
                portal_msg += '%s' % current_inspection_brains[0].Title
                for ci_brain in current_inspection_brains[1:]:
                    #portal_msg += ', <a href="%s">%s</a>' % (ci_brain.getURL(), ci_brain.Title)
                    portal_msg += ', %s' % ci_brain.Title

            api.portal.show_message(message=portal_msg,
                                    request=context.REQUEST,
                                    type='info')
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
        group_e_member_one = getattr(self, 'group_e_member_one', None)
        group_e_member_two = getattr(self, 'group_e_member_two', None)

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

        if group_e_member_one or group_e_member_two:
            if not three_teams:
                api.portal.show_message(message=u"You must configure Teams A, B, and C before Teams D or E.",
                                    request=context.REQUEST,
                                    type='warning')
                return False
            if not team_d:
                api.portal.show_message(message=u"You must configure Team D before Team E.",
                                    request=context.REQUEST,
                                    type='warning')
                return False

        return True

    def verifySecondInspectionComplete(self):
        context = self
        parent_container = context.aq_parent
        parent_container_path = '/'.join(parent_container.getPhysicalPath())
        current_inspection_brains = context.portal_catalog.searchResults(
                   path={'query': parent_container_path, 'depth': 3},
                   object_provides=IHOAHouseInspection.__identifier__,
                   review_state='failed_initial')
        if current_inspection_brains:
            house_inspection_title = getattr(context, 'house_inspection_title', '')
            current_inspections = []
            [current_inspections.append(i) for i in current_inspection_brains if i.getId == house_inspection_title]
            pending_inspections = len(current_inspections)
            pending_inspections = len(current_inspection_brains)
            portal_msg = ""
            if pending_inspections > 20:
                portal_msg += "There are %s homes remaining to inspect." % pending_inspections
            else:
                portal_msg += "The following homes have not been inspected: "
                #portal_msg += '<a href="%s">%s</a>' %(current_inspection_brains[0].getURL(), current_inspection_brains[0].Title)
                portal_msg += '%s' % current_inspection_brains[0].Title
                for ci_brain in current_inspection_brains[1:]:
                    #portal_msg += ', <a href="%s">%s</a>' % (ci_brain.getURL(), ci_brain.Title)
                    portal_msg += ', %s' % ci_brain.Title

            api.portal.show_message(message=portal_msg,
                                    request=context.REQUEST,
                                    type='info')
            return False

        return True

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
        pass_message_subject = "%s - Passed" % getattr(context, 'title', u'Annual Inspection')
        fail_message_subject = "%s - Failed" % getattr(context, 'title', u'Annual Inspection')

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
            city = getattr(pi_home_obj, 'city', '')
            state = getattr(pi_home_obj, 'state', '')
            zipcode = getattr(pi_home_obj, 'zipcode', '')
            address_string = "%s %s, %s %s, %s" % (street_number,
                                                   street_address,
                                                   city,
                                                   state,
                                                   zipcode)
            for ptn in people_to_email:
                member_data = api.user.get(userid=ptn)
                member_fullname = member_data.getProperty('fullname')
                member_email = member_data.getProperty('email')
                pass_message = "Dear %s,\n\n" % member_fullname
                pass_message += "Your home at: %s passed it's inspection.\n\n" % address_string
                pass_message += inspection_passed_message
                pass_message += "\n\nRegards,\n\nThe Meadows Board"

                api.portal.send_email(sender=secretary_email,
                                      recipient=member_email,
                                      subject=pass_message_subject,
                                      body=pass_message,
                                      immediate=True)

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
            address_string = "%s %s, %s %s, %s" % (street_number,
                                                   street_address,
                                                   city,
                                                   state,
                                                   zipcode)

            fieldsets = [ 'flowerpots', 'paint', 'sidewalk_drive', 'steps', 'decks_patio', 'general_maintenance' ]
            failure_dicts = []
            for fieldset in fieldsets:
                text = getattr(fi_obj, '%s_text' % fieldset, '')
                if text:
                    cond_remains = getattr(fi_obj, '%s_cond_remains' % fieldset, '')
                    image = getattr(fi_obj, '%s_image' % fieldset, None)
                    second_image = getattr(fi_obj, '%s_second_image', None)
                    f_dict = {'fieldset':fieldset,
                              'text':text,
                              'cond_remains':cond_remains,
                              'image':image,
                              'second_image':second_image
                              }
                    failure_dicts.append(f_dict)

            images_to_attach = []

            fail_message = ""
            fail_html = ""
            fail_message += "Your home at: %s failed it's inspection for the following reasons:\n\n" % address_string
            fail_html += "<p>Your home at: %s failed it's inspection for the following reasons:</p>" % address_string
            for failure_dict in failure_dicts:
                fail_message += '%s\n' % failure_dict.get('fieldset').title()
                fail_html += "<h4>%s</h4><ul>" % failure_dict.get('fieldset').title()
                if rewalk:
                    cond_remains = failure_dict.get('cond_remains')
                    if cond_remains:
                        fail_message += 'Condition Remains: YES\n'
                        fail_html += "<li>Condition Remains: YES</li>"
                    else:
                        fail_message += 'Condition Remains: NO\n'
                        fail_html += "<li>Condition Remains: NO</li>"
                fail_message += 'Failed for: %s\n\n' % failure_dict.get('text')
                fail_html += "<li>Failed for: %s</li></ul>" % failure_dict.get('text')

                first_image = failure_dict.get('image')
                if first_image:
                    images_to_attach.append(first_image)
                second_image = failure_dict.get('second_image')
                if second_image:
                    images_to_attach.append(second_image)


            fail_message += inspection_failure_message
            fail_html += "<p>%s</p>" % inspection_failure_message

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
                    img = MIMEImage(i_t_a.data)
                    msg.attach(img)

                send_message = "Dear %s,\n\n" % member_fullname
                send_message_html = "<p>Dear %s," % member_fullname
                send_message += fail_message
                send_message_html += fail_html

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

