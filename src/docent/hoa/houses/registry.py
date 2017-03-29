# -*- coding: utf-8 -*-
from plone import api
from plone.directives import form
from zope import schema

from docent.hoa.houses import _

import logging
logger = logging.getLogger("Plone")

def getDefaultDict():
    return dict()

class IHOAHomeLookupRegistry(form.Schema):
    """Global Blacklist Settings
    """

    hoa_owners = schema.Dict(
        title=_(u"Home Owners"),
        description=_(u"Each key value equals a list of home uuids"),
        key_type=schema.ASCIILine(title=_(u"Member Id")),
        value_type=schema.Set(title=_(u"House UUIDS"), value_type=schema.ASCIILine()),
        required=False,
        defaultFactory=getDefaultDict,)

    hoa_renters = schema.Dict(
        title=_(u"Home Owners"),
        description=_(u"Each key value equals a list of home uuids"),
        key_type=schema.ASCIILine(title=_(u"Member Id")),
        value_type=schema.Set(title=_(u"House UUIDS"), value_type=schema.ASCIILine()),
        required=False,
        defaultFactory=getDefaultDict,)

    hoa_property_managers = schema.Dict(
        title=_(u"Home Owners"),
        description=_(u"Each key value equals a list of home uuids"),
        key_type=schema.ASCIILine(title=_(u"Member Id")),
        value_type=schema.Set(title=_(u"House UUIDS"), value_type=schema.ASCIILine()),
        required=False,
        defaultFactory=getDefaultDict,)

    hoa_homes_by_uuid = schema.Dict(
        title=_(u"Home Owners"),
        description=_(u"Each key value equals a list of home uuids"),
        key_type=schema.ASCIILine(title=_(u"Home UUID")),
        value_type=schema.Dict(key_type=schema.ASCIILine(), value_type=schema.ASCIILine()),
        required=False,
        defaultFactory=getDefaultDict,)


def addCurrentHomeRoles(home_uuid, home_roles_dict):
    homes_by_uuid_dict = api.portal.get_registry_record('hoa_homes_by_uuid', interface=IHOAHomeLookupRegistry)
    if not homes_by_uuid_dict:
        homes_by_uuid_dict = {}
    homes_by_uuid_dict.update({home_uuid:home_roles_dict})
    api.portal.set_registry_record('hoa_homes_by_uuid', homes_by_uuid_dict, interface=IHOAHomeLookupRegistry)


def addHomeToLookupRegistry(member_id, home_uuid, property_role):
    home_lookup_dict = api.portal.get_registry_record(property_role, interface=IHOAHomeLookupRegistry)
    if not home_lookup_dict:
        home_lookup_dict = {}
    member_homes_by_uuid = home_lookup_dict.get(member_id, set())
    member_homes_by_uuid.add(home_uuid)
    home_lookup_dict.update({member_id:member_homes_by_uuid})

    api.portal.set_registry_record(property_role, home_lookup_dict, interface=IHOAHomeLookupRegistry)


def removeHomeFromLookupRegistry(member_id, home_uuid, property_role):
    home_lookup_dict = api.portal.get_registry_record(property_role, interface=IHOAHomeLookupRegistry)
    if not home_lookup_dict:
        home_lookup_dict = {}
    member_homes_by_uuid = home_lookup_dict.get(member_id, set())
    try:
        member_homes_by_uuid.remove(home_uuid)
    except KeyError:
        logger.warn("HOA HOUSES: home with %s not listed for %s" % (home_uuid, member_id))
        return

    home_lookup_dict.update({member_id:member_homes_by_uuid})
    api.portal.set_registry_record(property_role, home_lookup_dict, interface=IHOAHomeLookupRegistry)


def clearAllHomesForMember(member_id, property_role=None):
    if property_role:
        home_lookup_dict = api.portal.get_registry_record(property_role, interface=IHOAHomeLookupRegistry)
        if not home_lookup_dict:
            home_lookup_dict = {}
        member_homes_by_uuid = home_lookup_dict.get(member_id, set())
        member_homes_by_uuid.clear()
        home_lookup_dict.update({member_id:member_homes_by_uuid})
        api.portal.set_registry_record(property_role, home_lookup_dict, interface=IHOAHomeLookupRegistry)
    else:
        for p_role in ['hoa_owners', 'hoa_renters', 'hoa_property_managers']:
            home_lookup_dict = api.portal.get_registry_record(p_role, interface=IHOAHomeLookupRegistry)
            if not home_lookup_dict:
                home_lookup_dict = {}
            member_homes_by_uuid = home_lookup_dict.get(member_id, set())
            if not member_homes_by_uuid:
                member_homes_by_uuid = {}
            member_homes_by_uuid.clear()
            home_lookup_dict.update({member_id:member_homes_by_uuid})
            api.portal.set_registry_record(p_role, home_lookup_dict, interface=IHOAHomeLookupRegistry)