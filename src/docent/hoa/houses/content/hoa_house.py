import logging
from plone import api
from plone.dexterity.content import Container
from plone.directives import form
from plone.indexer import indexer
from plone.namedfile.field import NamedBlobImage
from plone.supermodel.directives import fieldset
from zope import schema
from zope.interface import provider, invariant, Invalid
from zope.schema.interfaces import IContextAwareDefaultFactory

from docent.hoa.houses.registry import IHOAHomeLookupRegistry
from docent.hoa.houses.app_config import HOME_ROLE_TO_ATTRIBUTE_LOOKUP_DICT
from docent.hoa.houses.registry import (addHomeToLookupRegistry,
                                        removeHomeFromLookupRegistry,
                                        clearAllHomesForMember,
                                        addCurrentHomeRoles)

from docent.hoa.houses import _

logger = logging.getLogger("Plone")

ROLE_IDS = ['owner_one', 'owner_two',
            'resident_one', 'resident_two',
            'property_manager', ]

@provider(IContextAwareDefaultFactory)
def getNeighborhoodState(context):
    """
    If called from an add view, the container will be the context,
    however if called from an edit view, the context will be the
    hoa_house so we need find the actual hoa_neighborhood
    in order to search for active clubs
    """
    if context.portal_type == "hoa_neighborhood":
        parent_container = context
    else:
        parent_container = context.aq_parent

    #if the parent_container is not a neighborhood, give up!
    if parent_container.portal_type != "hoa_neighborhood":
        return u""

    default_state = getattr(parent_container, 'state', u'')

    return default_state

@provider(IContextAwareDefaultFactory)
def getNeighborhoodZipCode(context):
    """
    If called from an add view, the container will be the context,
    however if called from an edit view, the context will be the
    hoa_house so we need find the actual hoa_neighborhood
    in order to search for active clubs
    """
    if context.portal_type == "hoa_neighborhood":
        parent_container = context
    else:
        parent_container = context.aq_parent

    #if the parent_container is not a neighborhood, give up!
    if parent_container.portal_type != "hoa_neighborhood":
        return u""
    default_zip = getattr(parent_container, 'zipcode', u'')

    return default_zip

@provider(IContextAwareDefaultFactory)
def getNeighborhoodCity(context):
    """
    If called from an add view, the container will be the context,
    however if called from an edit view, the context will be the
    hoa_house so we need find the actual hoa_neighborhood
    in order to search for active clubs
    """
    if context.portal_type == "hoa_neighborhood":
        parent_container = context
    else:
        parent_container = context.aq_parent

    #if the parent_container is not a neighborhood, give up!
    if parent_container.portal_type != "hoa_neighborhood":
        return u""
    default_city = getattr(parent_container, 'city', u'')

    return default_city


class IHOAHouse(form.Schema):
    """
    """

    fieldset('house_information',
        label=u'House Information',
        description=u'Home details',
        fields=['title',
                'div',
                'lot',
                'street_number',
                'street_address',
                'city',
                'state',
                'zipcode',
                'picture',
                'geo_coordinates_lat',
                'geo_coordinates_long',
                'last_sale_date',
                'rental', ]
    )

    form.mode(title='hidden')
    title = schema.TextLine(
        title=_(u"Title"),
        required=False,
    )

    div = schema.Choice(
        title=_(u"Division Number"),
        description=_(u""),
        vocabulary=u'docent.hoa.div_numbers',
        required=False,
    )

    lot = schema.Choice(
        title=_(u"Lot Number"),
        description=_(u""),
        vocabulary=u'docent.hoa.lot_numbers',
        required=False,
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

    city = schema.TextLine(
        title=_(u"City"),
        description=_(u"Please provide the city to be used with addresses in this neighborhood."),
        defaultFactory=getNeighborhoodCity,
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

    geo_coordinates_lat = schema.TextLine(
        title=_(u"Geo Coordinates Latitude"),
        description=_(u""),
        required=False,
    )

    geo_coordinates_long = schema.TextLine(
        title=_(u"Geo Coordinates Longitude"),
        description=_(u""),
        required=False,
    )

    last_sale_date = schema.Date(
        title=_(u"Last Sale Date"),
        description=_(u""),
        required=False,
    )

    rental = schema.Bool(
        title=_(u'Is this a rental property?'),
        description=_(u''),
        required=False,
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
        required=False,
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
        required=False,
    )

    resident_two = schema.Choice(
        title=_(u"Resident Two"),
        description=_(u""),
        vocabulary=u'docent.hoa.renters',
        required=False,
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
        required=False,
    )

    @invariant
    def ownersInvariant(data):
        owner_one = data.owner_one
        owner_two = data.owner_two
        if owner_one and owner_two:
            if owner_one == owner_two:
                raise Invalid(_(u"Owners One and Two cannot be the same individual."))

    @invariant
    def residentInvariant(data):
        resident_one = data.resident_one
        resident_two = data.resident_two
        if resident_one and resident_two:
            if resident_one == resident_two:
                raise Invalid(_(u"Resident One and Two cannot be the same individual."))

    @invariant
    def lotInvariant(data):
        lot = data.lot
        try:
            int(lot)
        except ValueError:
            raise Invalid(_(u"Lot is not a valid number."))
        if len(lot) != 3:
            raise Invalid(_(u"Lot is not in the correct format (ie 045 for lot 45)"))



@indexer(IHOAHouse)
def streetNumberIndexer(obj):
    if obj.street_number is None:
        return None
    return obj.street_number

@indexer(IHOAHouse)
def streetAddressIndexer(obj):
    if obj.street_address is None:
        return None
    return obj.street_address

@indexer(IHOAHouse)
def ownerOneIndexer(obj):
    if obj.owner_one is None:
        return None
    return obj.owner_one

@indexer(IHOAHouse)
def ownerTwoIndexer(obj):
    if obj.owner_two is None:
        return None
    return obj.owner_two

@indexer(IHOAHouse)
def residentOneIndexer(obj):
    if obj.resident_one is None:
        return None
    return obj.resident_one

@indexer(IHOAHouse)
def residentTwoIndexer(obj):
    if obj.resident_two is None:
        return None
    return obj.resident_two

@indexer(IHOAHouse)
def propertyManagerIndexer(obj):
    if obj.street_address is None:
        return None
    return obj.property_manager



class HOAHouse(Container):
    """
    """
    def after_object_added_processor(self, context, event):
        self.update_role_members()

    def after_edit_processor(self):
        self.update_role_members()
        self.update_rental_status()

    def remove_member_from_home_roles(self, member_id):
        for r_id in ROLE_IDS:
            assigned_id = getattr(self, r_id, '')
            if assigned_id == member_id:
                setattr(self, r_id, '')

    def update_rental_status(self):
        resident_one = getattr(self, 'resident_one', '')
        resident_two = getattr(self, 'resident_two', '')
        if not resident_one and not resident_two:
            setattr(self, 'rental', False)
        else:
            setattr(self, 'rental', True)

    def update_role_members(self):
        """
        look up each member by their role and associate house with that member
        """
        context = self
        context_uuid = api.content.get_uuid(obj=context)
        #get roles data
        # owner_one = getattr(context, 'owner_one', '')
        # owner_two = getattr(context, 'owner_two', '')
        # resident_one = getattr(context, 'resident_one', '')
        # resident_two = getattr(context, 'resident_two', '')
        # property_manager = getattr(context, 'property_manager', '')

        homes_by_uuid_dict = api.portal.get_registry_record('hoa_homes_by_uuid', interface=IHOAHomeLookupRegistry)
        if not homes_by_uuid_dict:
            homes_by_uuid_dict = {}
        previous_values_dict = homes_by_uuid_dict.get(context_uuid, {})
        current_values_dict = {}
        for role_id in ROLE_IDS:
            member_id = getattr(context, role_id, '')
            if not member_id:
                member_id = ''
            current_values_dict.update({role_id:member_id})

        if current_values_dict == previous_values_dict:
            return

        for r_id in ROLE_IDS:
            new_value = current_values_dict.get(r_id, '')
            old_value = previous_values_dict.get(r_id, '')
            property_role = HOME_ROLE_TO_ATTRIBUTE_LOOKUP_DICT.get(r_id)
            if new_value != old_value:
                if old_value:
                    removeHomeFromLookupRegistry(old_value, context_uuid, property_role)
                if new_value:
                    addHomeToLookupRegistry(new_value, context_uuid, property_role)

        addCurrentHomeRoles(context_uuid, current_values_dict)

