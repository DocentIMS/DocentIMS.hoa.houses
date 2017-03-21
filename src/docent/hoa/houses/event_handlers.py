# -*- coding: utf-8 -*-
from zope.component import adapter
from Products.PluggableAuthService.interfaces.events import (IPrincipalCreatedEvent,
                                                             IPrincipalDeletedEvent,
                                                             IPropertiesUpdatedEvent)

def after_edit_processor(context, event):
    if hasattr(context, 'after_edit_processor'):
        context.after_edit_processor()

def after_transition_processor(context, event):
    if hasattr(context, 'after_transition_processor'):
        context.after_transition_processor()

def after_creation_processor(context, event):
    if hasattr(context, 'after_creation_processor'):
        context.after_creation_processor(context, event)

def after_object_added_processor(context, event):
    if hasattr(context, 'after_object_added_processor'):
        context.after_object_added_processor(context, event)


@adapter(IPrincipalCreatedEvent)
def onPrincipalCreation(event):
    """
    assign member to house
    """
    #event.principal, event.principal.getUserId()

@adapter(IPrincipalDeletedEvent)
def onPrincipalDeletion(event):
    """
    find member house and remove member from home
    """

@adapter(IPropertiesUpdatedEvent)
def onPrincipalUpdate(event):
    """
    find member house and update member
    """
