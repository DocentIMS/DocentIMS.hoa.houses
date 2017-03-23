# -*- coding: utf-8 -*-

#Default Group Ids
BOARD_MEMBERS_GID = 'board_members'
HOME_OWNERS_GID = 'home_owners'
RENTERS_GID = 'renters'
PROPERTY_MANAGERS_GID = 'property_managers'

GROUP_TITLE_DICT = {BOARD_MEMBERS_GID: u'Board Members',
                    HOME_OWNERS_GID: u'Home Owners',
                    RENTERS_GID: u'Renters',
                    PROPERTY_MANAGERS_GID: u'Property Managers', }

PROPERTY_ROLE_DICT = {HOME_OWNERS_GID: u'Owner',
                      RENTERS_GID: u'Renter',
                      PROPERTY_MANAGERS_GID: u'Property Manager'}

PROPERTY_ROLE_TO_HOME_ATTRIBUTE_LOOKUP_DICT = {HOME_OWNERS_GID: ['owner_one', 'owner_two'],
                      RENTERS_GID: ['resident_one', 'resident_two'],
                      PROPERTY_MANAGERS_GID: ['property_manager']}


HOME_ROLE_TO_ATTRIBUTE_LOOKUP_DICT = {'owner_one':'hoa_owners',
                                      'owner_two':'hoa_owners',
                                      'resident_one':'hoa_renters',
                                      'resident_two':'hoa_renters',
                                      'property_manager':'hoa_property_managers'}