import logging
from Acquisition import aq_base
from plone import api
from plone.dexterity.content import Container
from plone.directives import form
from plone.supermodel.directives import fieldset
from zope import schema
from plone.schema import Email

from docent.hoa.houses import _

from docent.hoa.houses.app_config import DIVISION_ONE, DIVISION_TWO, WALKERS_GROUP_IDS

logger = logging.getLogger("Plone")

class IHOANeighborhood(form.Schema):
    """Uses IDublinCore
    """

    street_addresses = schema.List(
        title=_(u"Street Addresses"),
        description=_(u"Please provide a list of street addresses for this neighborhood."),
        value_type=schema.TextLine(),
    )

    city = schema.TextLine(
        title=_(u"City"),
        description=_(u"Please provide the city to be used with addresses in this neighborhood.")
    )

    state = schema.TextLine(
        title=_(u"State Abbreviation"),
        description=_(u"Please provide the state abbreviation to be used with addresses in this neighborhood.")
    )

    zipcode = schema.TextLine(
        title=_(u"Zipcode"),
        description=_(u"Which zipcode does this neighborhood use?")
    )

    secretary_email = Email(
        title=_(u"Executive Secretary Email"),
        description=_(u"Email address of the Executive Secretary"),
        required=True,
    )

    fieldset('initial_messages',
        label=u'Initial Inspection Messages',
        description=u'',
        fields=['initial_pass_message',
                'initial_fail_message',]
    )

    initial_pass_message = schema.Text(
        title=_(u"Initial Passed Inspection Message"),
        description=_(u"This message is used for both email and postal messages to be sent."),
        required=False,
    )

    initial_fail_message = schema.Text(
        title=_(u"Initial Fail Inspection Message"),
        description=_(u"This message is used for both email and postal messages to be sent."),
        required=False,
    )

    fieldset('rewalk_messages',
        label=u'Re-walk Inspection Messages',
        description=u'',
        fields=['rewalk_pass_message',
                'rewalk_fail_message',]
    )

    rewalk_pass_message = schema.Text(
        title=_(u"Rewalk Passed Inspection Message"),
        description=_(u"This message is used for both email and postal messages to be sent."),
        required=False,
    )

    rewalk_fail_message = schema.Text(
        title=_(u"Rewalk Fail Message"),
        description=_(u"This message is used for both email and postal messages to be sent."),
        required=False,
    )


class HOANeighborhood(Container):
    """
    """

    def after_object_added_processor(self, context, event):
        context = self
        #all_house_ids = DIVISION_ONE + DIVISION_TWO
        all_house_ids = ['1_001', '1_002', '1_003', '1_004', '1_005']
        for house_id in all_house_ids:
            div, lot = house_id.split('_')
            house_obj = api.content.create(container=context,
                                           type='hoa_house',
                                           title=house_id,
                                           div=div,
                                           lot=lot)
            aq_base(house_obj).__ac_local_roles_block = True

        for g_id in WALKERS_GROUP_IDS:
            api.group.grant_roles(groupname=g_id,
                                  roles=['Reader'],
                                  obj=context)
        context.reindexObjectSecurity()
