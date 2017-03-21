import logging

from plone.dexterity.content import Container
from plone.directives import form
from plone.namedfile.field import NamedBlobImage
from plone.supermodel.directives import fieldset
from zope import schema
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory
from docent.hoa.houses import _

logger = logging.getLogger("Plone")

@provider(IContextAwareDefaultFactory)
def getNeighborhoodState(context):
    parent = context.aq_parent
    default_state = getattr(parent, 'state', u'')

    return default_state

@provider(IContextAwareDefaultFactory)
def getNeighborhoodZipCode(context):
    parent = context.aq_parent
    default_state = getattr(parent, 'zipcode', u'')

    return default_state


class IHOAHouse(form.Schema):
    """
    """

    form.mode(title='hidden')
    title = schema.TextLine(
        title=_(u"Title")
    )

    fieldset('house_information',
        label=u'House Information',
        description=u'Home details',
        fields=['div',
                'lot',
                'street_number',
                'street_address',
                'state',
                'zipcode',
                'picture',
                'geo_coordinates',
                'last_sale_date',
                'rental', ]
    )

    div = schema.ASCIILine(
        title=_(u"Division"),
        description=_(u"HOA Division")
    )

    lot = schema.ASCIILine(
        title=_(u"Lot"),
        description=_(u"HOA LOT Number")
    )

    street_number = schema.TextLine(
        title=_(u"Street Number"),
        description=_(u"")
    )

    street_address = schema.Choice(
        title=_(u"Street Address"),
        description=_(u""),
        vocabulary=u'docent.hoa.street_addresses',
    )

    state = schema.TextLine(
        title=_(u"State Abbreviation"),
        description=_(u"Please provide the state abbreviation to be used with addresses in this neighborhood."),
        defaultFactory=getNeighborhoodState,
    )

    zipcode = schema.TextLine(
        title=_(u"Zipcode"),
        description=_(u"Which zipcode does this neighborhood use?"),
        defaultFactory=getNeighborhoodZipCode,
    )

    picture = NamedBlobImage(
        title=_(u"Upload an image of the home."),
        required=False,
    )

    geo_coordinates = schema.TextLine(
        title=_(u"Geo Coordinates"),
        description=_(u""),
    )

    last_sale_date = schema.Date(
        title=_(u"Last Sale Date"),
        description=_(u"")
    )

    rental = schema.Bool(
        title=_(u'Is this a rental property?'),
        description=_(u''),
    )

    fieldset('owner_information',
        label=u'Owner Information',
        description=u'Owner details',
        fields=['owner_one',
                'owner_two', ]
    )

    owner_one = schema.Choice(
        title=_(u"Owner One"),
        description=_(u""),
        vocabulary=u'docent.hoa.home_owner',
    )

    owner_two = schema.Choice(
        title=_(u"Owner Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.home_owner',
    )

    fieldset('resident_information',
        label=u'Resident Information',
        description=u'Resident details',
        fields=['resident_one',
                'resident_two', ]
    )

    resident_one = schema.Choice(
        title=_(u"Resident One"),
        description=_(u""),
        vocabulary=u'docent.hoa.renters',
    )

    resident_two = schema.Choice(
        title=_(u"Resident Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.renters',
    )

    fieldset('property_manager',
        label=u'Propertry Manager',
        description=u'',
        fields=['property_manager', ]
    )

    property_manager = schema.Choice(
        title=_(u"Property Manager"),
        description=_(u""),
        vocabulary=u'docent.hoa.property_managers',
    )


class HOAHouse(Container):
    """
    """
