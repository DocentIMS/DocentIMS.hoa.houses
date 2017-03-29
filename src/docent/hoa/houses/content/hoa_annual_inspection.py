import logging
from datetime import date
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

from docent.hoa.houses.content.hoa_house import IHOAHouse
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
        required=False,
    )
    
    end_date = schema.Date(
        title=_(u"End Date"),
        description=_(u"This field is calculated at the end of the Annual Inspection"),
        required=False,
    )

    rental = schema.Bool(
        title=_(u'Picture Rqd if Failed?'),
        description=_(u''),
        required=False,
    )

    number_of_groups = schema.Choice(
        title=_(u"Number of Groups"),
        description=_(u""),
        vocabulary=group_numbers_vocab,
        required=True,
    )

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
    )

    group_a_member_two = schema.Choice(
        title=_(u"Group A Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
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
    )

    group_b_member_two = schema.Choice(
        title=_(u"Group B Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
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
    )

    group_c_member_two = schema.Choice(
        title=_(u"Group C Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
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
    )

    group_d_member_two = schema.Choice(
        title=_(u"Group D Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
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
    )

    group_e_member_two = schema.Choice(
        title=_(u"Group E Member Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.walkers',
        required=False,
    )



class HOAAnnualInspection(Container):
    """
    """

    def after_object_added_processor(self, context, event):
        self.generate_house_inspection_title()

    def after_transition_processor(self):
        context_state = api.content.get_state(obj=self)
        if context_state == 'initial_inspection':
            self.propagate_house_inspections()
            self.assign_security()

    def assign_security(self):
        context = self
        parent_container = context.aq_parent
        if parent_container.portal_type != "hoa_neighborhood":
            #woah something went wrong
            return
        number_of_groups = getattr(context, 'number_of_groups', 3)
        lot_division_dict = LOT_DIVISION_DICT.get(number_of_groups)
        for walker_group_id in lot_division_dict:
            homes_assigned_by_id = lot_division_dict.get(walker_group_id)
            for home_id in homes_assigned_by_id:
                home_obj = parent_container.get(home_id)
                if home_obj:
                    #clear previous group roles
                    home_obj.manage_delLocalRoles(WALKERS_GROUP_IDS)
                    #set new role
                    api.group.grant_roles(groupname=walker_group_id,
                                          roles=['Editor'],
                                          obj=home_obj)
                    home_obj.reindexObjectSecurity()

    def generate_house_inspection_title(self):
        today = date.today()
        setattr(self, 'house_inspection_title', today.strftime('%Y-%m'))

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
            house_inspection_title = today.strftime('%Y-%m')

        added_inspections = 0
        for house_brain in house_brains:
            house_obj = house_brain.getObject()
            api.content.create(container=house_obj,
                               type='hoa_house_inspection',
                               id=house_inspection_title,
                               title=u'House Inspection %s' % house_inspection_title,
                               safe_id=True)
            added_inspections += 1

        api.portal.show_message(message=u"%s houses prepared for annual inspection." % added_inspections,
                                request=context.REQUEST,
                                type='info')