
from plone import api
from plone.api.exc import GroupNotFoundError
from Products.CMFCore.utils import getToolByName
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory
from zope.interface import implementer

from docent.hoa.houses.app_config import (BOARD_MEMBERS_GID,
                                          HOME_OWNERS_GID,
                                          RENTERS_GID,
                                          PROPERTY_MANAGERS_GID,
                                          PROPERTY_ROLE_DICT)

from docent.hoa.houses.content.hoa_house import IHOAHouse

def getGroupMemberVocabulary(group_name):
    """Return a set of groupmembers, return an empty set if group not found
    """
    try:
        group_members = api.user.get_users(groupname=group_name)
    except GroupNotFoundError:
        group_members = ()

    member_fullname_by_id_dict = {}
    for member_data in group_members:
        member_id = member_data.getId()
        member_fullname = member_data.getProperty('fullname')
        member_fullname_by_id_dict.update({member_id:member_fullname})

    terms = []

    if member_fullname_by_id_dict:
        terms.append(SimpleVocabulary.createTerm('', '', 'Choose One'))
        for id_key, name_value in sorted(member_fullname_by_id_dict.iteritems(), key=lambda (k,v): (v,k)):
            terms.append(SimpleVocabulary.createTerm(id_key, str(id_key), name_value))
    else:
        terms.append(SimpleVocabulary.createTerm('', '', 'No Members'))

    return SimpleVocabulary(terms)

@implementer(IVocabularyFactory)
class IBoardMemberVocabulary(object):
    def __call__(self, context):
        return getGroupMemberVocabulary(BOARD_MEMBERS_GID)
IBoardMemberVocabularyFactory = IBoardMemberVocabulary()

@implementer(IVocabularyFactory)
class IHomeOwnerVocabulary(object):
    def __call__(self, context):
        return getGroupMemberVocabulary(HOME_OWNERS_GID)
IHomeOwnerVocabularyFactory = IHomeOwnerVocabulary()

@implementer(IVocabularyFactory)
class IRentersVocabulary(object):
    def __call__(self, context):
        return getGroupMemberVocabulary(RENTERS_GID)
IRentersVocabularyFactory = IRentersVocabulary()

@implementer(IVocabularyFactory)
class IPropertyManagersVocabulary(object):
    def __call__(self, context):
        return getGroupMemberVocabulary(PROPERTY_MANAGERS_GID)
IPropertyManagersVocabularyFactory = IPropertyManagersVocabulary()

@implementer(IVocabularyFactory)
class IPropertyRoleVocabulary(object):
    def __call__(self, context):
        terms = []
        terms.append(SimpleVocabulary.createTerm('', '', 'Choose A Property Role'))
        for role_key in PROPERTY_ROLE_DICT.keys():
            terms.append(SimpleVocabulary.createTerm(role_key, str(role_key), PROPERTY_ROLE_DICT.get(role_key, u'')))

        return SimpleVocabulary(terms)
IPropertyRoleVocabularyFactory = IPropertyRoleVocabulary()

@implementer(IVocabularyFactory)
class IHousesVocabulary(object):
    """
    build a vocabulary based on Houses
    """
    def __call__(self, context):
        """
        If called from an add view, the container will be the context,
        however if called from an edit view, the context will be the
        attendance_record so we need find the actual booster_clubs_folder
        in order to search for active clubs
        """
        portal = api.portal.get()
        catalog = getToolByName(portal, 'portal_catalog')

        house_brains = catalog(object_provides=IHOAHouse.__identifier__,
                               sort_on='getObjPositionInParent',
                               sort_on='sortable_title',
                               sort_order='ascending')

        terms = []
        if house_brains:
            terms.append(SimpleVocabulary.createTerm('', '', 'Choose A Home'))
            for house_brain in house_brains:
                house_uid = house_brain.UID
                house_title = house_brain.Title
                terms.append(SimpleVocabulary.createTerm(house_uid, str(house_uid), house_title))
        else:
            terms.append(SimpleVocabulary.createTerm('', '', 'No Homes'))

        return SimpleVocabulary(terms)
IHousesVocabularyFactory = IHousesVocabulary()

@implementer(IVocabularyFactory)
class IStreetAddressVocabulary(object):
    """
    build a vocabulary based on the street addresses attribute set in HOA Neighborhood.
    """
    def __call__(self, context):
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

        #if the parent_container is not a booster_clubs_folder, give up!
        if parent_container.portal_type != "hoa_neighborhood":
            return SimpleVocabulary([SimpleVocabulary.createTerm('', '', 'HOA Neighborhood Not Found')])

        street_addresses = getattr(parent_container, 'street_addresses', [])
        terms = []

        if street_addresses:
            terms.append(SimpleVocabulary.createTerm('', '', 'Choose A Street'))
            for street_address in street_addresses:
                terms.append(SimpleVocabulary.createTerm(street_address, str(street_address), street_address))
        else:
            terms.append(SimpleVocabulary.createTerm('', '', 'No Configured Addresses'))

        return SimpleVocabulary(terms)
IStreetAddressVocabularyFactory = IStreetAddressVocabulary()