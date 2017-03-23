# -*- coding: utf-8 -*-
from plone.app.content.interfaces import INameFromTitle
from zope.component import adapts
from zope.interface import implements, Interface

class INameFromDivAndLot(Interface):
    """ Interface to adapt to INameFromTitle """

class NameFromDivAndLot(object):
    """ Adapter to INameFromTitle """
    implements(INameFromTitle)
    adapts(INameFromDivAndLot)

    def __init__(self, context):
        pass

    def __new__(cls, context):
        div = getattr(context, 'div', 'div')
        lot = getattr(context, 'lot', 'lot')

        title = u'%s %s' % (div, lot)
        inst = super(NameFromDivAndLot, cls).__new__(cls)

        inst.title = title
        context.setTitle(title)

        return inst