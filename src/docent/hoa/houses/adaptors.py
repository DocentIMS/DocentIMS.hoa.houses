# from plone.app.content.interfaces import INameFromTitle
# from zope.interface import implements
#
# class INameFromDivLot(INameFromTitle):
#     def title():
#         """Return a processed title"""
#
# class NameFromDivLot(object):
#     implements(INameFromDivLot)
#
#     def __init__(self, context):
#         self.context = context
#
#     @property
#     def title(self):
#         div = getattr(self.context, 'div', 'div')
#         lot = getattr(self.context, 'lot', 'lot')
#         return '%s %s' % (div, lot)