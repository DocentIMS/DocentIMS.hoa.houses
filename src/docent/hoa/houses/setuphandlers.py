# -*- coding: utf-8 -*-
from plone import api
from plone.api.exc import GroupNotFoundError
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer

from docent.hoa.houses.app_config import GROUP_TITLE_DICT

@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller"""
        return [
            'docent.hoa.houses:uninstall',
        ]


def post_install(context):
    """Post install script"""
    # create base groups if they do not exist
    group_ids = GROUP_TITLE_DICT.keys()
    for group_id in group_ids:
        try:
            group = api.group.get(groupname=group_id)
        except GroupNotFoundError:
            group = api.group.create(groupname=group_id,
                                     title=GROUP_TITLE_DICT.get(group_id, u''))

        if not group:
            api.group.create(groupname=group_id,
                             title=GROUP_TITLE_DICT.get(group_id, u''))


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
