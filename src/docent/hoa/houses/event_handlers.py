# -*- coding: utf-8 -*-
from zope.component import adapter
from plone import api
from Products.CMFCore.interfaces import IMemberData
from docent.hoa.houses.content.hoa_house import IHOAHouse
from docent.hoa.houses.content.hoa_house import ROLE_IDS
from docent.hoa.houses.registry import IHOAHomeLookupRegistry
from docent.hoa.houses.app_config import PROPERTY_ROLE_DICT, PROPERTY_ROLE_TO_HOME_ATTRIBUTE_LOOKUP_DICT, WALKERS_GROUP_IDS

import logging
logger = logging.getLogger("Plone")


def after_edit_processor(context, event):
    logger.info('after_edit_processor')
    if hasattr(context, 'after_edit_processor'):
        context.after_edit_processor()

def after_transition_processor(context, event):
    logger.info('after_transition_processor')
    if hasattr(context, 'after_transition_processor'):
        context.after_transition_processor()

def after_creation_processor(context, event):
    logger.info('after_creation_processor')
    if hasattr(context, 'after_creation_processor'):
        context.after_creation_processor(context, event)

def after_object_added_processor(context, event):
    logger.info('after_object_added_processor')
    if hasattr(context, 'after_object_added_processor'):
        context.after_object_added_processor(context, event)


def logged_in_handler(event):
    #get the currently logged in member
    current_member = api.user.get_current()
    current_member_groups = api.group.get_groups(user=current_member)
    member_fullname = current_member.getProperty('fullname')

    logger.info("Login event for: %s" % member_fullname)
    for mgroup in current_member_groups:
        if mgroup.getId() in WALKERS_GROUP_IDS:
            logger.info("Login event: %s is a weedwalker.")
            portal = api.portal.get()
            neighborhood_objs = portal.listFolderContents(contentFilter={"portal_type":"hoa_neighborhood",
                                                                         "sort_on":"created",
                                                                         "sort_order":"ascending"})
            if neighborhood_objs and len(neighborhood_objs) == 1:
                n_obj = neighborhood_objs[0]
                #is there an open inspection?
                inspections = n_obj.listFolderContents(contentFilter={"portal_type":"hoa_annual_inspection",
                                                                      "sort_on":"created",
                                                                      "sort_order":"ascending"})
                if inspections:
                    current_inspection = inspections[0]
                    ci_state = api.content.get_state(obj=current_inspection)
                    if ci_state != 'closed':
                        logger.info("Login event: redirecting %s to walker-assignments." % member_fullname)
                        request = portal.REQUEST
                        response = request.response
                        return response.redirect('%s/@@walker-assignments' % n_obj.absolute_url())
                    else:
                        logger.warn("Login event: There are no active inspections.")
            else:
                logger.warn("Login event: There are too many neighborhoods to redirect to.")


#@adapter(IPrincipalCreatedEvent)
def onPrincipalCreation(context, event):
    """
    assign member to house
    """
    #event.principal, event.principal.getUserId()
    logger.info('onPrincipalCreation')
    

#@adapter(IPrincipalDeletedEvent)
def onPrincipalDeletion(event):
    """
    find member house and remove member from home
    """
    logger.info('onPrincipalDeletion starting')
    member_id = getattr(event, 'principal', '')
    if member_id:
        homes_to_check = set()
        for p_role in ['hoa_owners', 'hoa_renters', 'hoa_property_managers']:
            home_lookup_dict = api.portal.get_registry_record(p_role, interface=IHOAHomeLookupRegistry)
            member_homes_by_uuid = home_lookup_dict.get(member_id, set())
            homes_to_check = homes_to_check|member_homes_by_uuid
        for mh_uuid in homes_to_check:
            mh = api.content.get(UID=mh_uuid)
            mh.remove_member_from_home_roles(member_id)
            mh.update_role_members()
            mh.update_rental_status()
            mh.reindexObject()

        # home_lookup_dict.pop(member_id, None)
        # api.portal.set_registry_record(p_role, home_lookup_dict, interface=IHOAHomeLookupRegistry)

logger.info('onPrincipalDeletion complete')

# #@adapter(IPropertiesUpdatedEvent)
# def onPrincipalUpdate(event):
#     """
#     find member house and update member
#     """
#     logger.info('HOA.HOUSES: starting event: onPrincipalUpdate')
    # if hasattr(event, 'context'):
    #     context = event.context
    #     if hasattr(context, 'member'):
    #         member_data = context.member
    #         if IMemberData.providedBy(member_data):
    #             #check primary group
    #             primary_role = member_data.getProperty('property_role')
    #             if primary_role:
    #                 member_groups = api.group.get_groups(user=member_data)
    #                 group_ids = []
    #                 [group_ids.append(group_data.getId()) for group_data in member_groups]
    #                 if primary_role not in group_ids:
    #                     default_group_ids = PROPERTY_ROLE_DICT.keys()
    #                     g_id = default_group_ids.pop(primary_role)
    #                     #add member to group
    #                     api.group.add_user(groupname=g_id, user=member_data)
    #                     #remove member from other groups
    #                     for remaining_g_id in default_group_ids:
    #                         api.group.remove_user(groupname=remaining_g_id, user=member_data)
    #
    #             home_uuid = member_data.getProperty('hoa_home_uuid')
    #             member_id = member_data.getId()
    #             if home_uuid:
    #                 hoa_house = api.content.get(UID=home_uuid)
    #                 if IHOAHouse.providedBy(hoa_house):
    #                     fields_to_check = PROPERTY_ROLE_TO_HOME_ATTRIBUTE_LOOKUP_DICT.get(primary_role)
    #                     if fields_to_check:
    #                         member_configured = False
    #                         fields_configured = []
    #                         for f_t_c in fields_to_check:
    #                             set_member = getattr(hoa_house, f_t_c, '')
    #                             if set_member:
    #                                 fields_configured.append(f_t_c)
    #                                 if set_member == member_id:
    #                                     member_configured = True
    #
    #                         if not member_configured:
    #                             if len(fields_configured) == len(fields_to_check):
    #                                 #we can't do anything...
    #                                 fullname = member_data.getProperty('fullname')
    #                                 api.portal.show_message(type='warning',
    #                                                         message='%s cannot be added to home: %s as there are '
    #                                                                 'currently the maximum members set at that '
    #                                                                 'location. Please update the member '
    #                                                                 'information at the home' % (fullname,
    #                                                                                              hoa_house.title))
    #                             else:
    #                                 if len(fields_configured) == 1:
    #                                     field_configured = fields_configured[0]
    #                                     fields_to_check.pop(field_configured)
    #                                     remaining_field = fields_to_check[0]
    #                                     setattr(hoa_house, remaining_field, member_id)
    #                                 elif not fields_configured:
    #                                     field_to_set = fields_to_check[0]
    #                                     setattr(hoa_house, field_to_set, member_id)
    #
    #
