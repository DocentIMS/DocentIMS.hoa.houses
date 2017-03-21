import logging

from plone.dexterity.content import Container
from plone.directives import form
from zope import schema
from docent.hoa.houses import _

logger = logging.getLogger("Plone")

class IHOANeighborhood(form.Schema):
    """
    """

    street_addresses = schema.List(
        title=_(u"Street Addresses"),
        description=_(u"Please provide a list of street addresses for this neighborhood."),
        value_type=schema.TextLine(),
    )

    state = schema.TextLine(
        title=_(u"State Abbreviation"),
        description=_(u"Please provide the state abbreviation to be used with addresses in this neighborhood.")
    )

    zipcode = schema.TextLine(
        title=_(u"Zipcode"),
        description=_(u"Which zipcode does this neighborhood use?")
    )


class HOANeighborhood(Container):
    """
    """
