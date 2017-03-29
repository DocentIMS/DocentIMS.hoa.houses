import logging
from plone import api
from plone.dexterity.content import Container
from plone.directives import form
from zope import schema
from docent.hoa.houses import _

from docent.hoa.houses.app_config import DIVISION_ONE, DIVISION_TWO

logger = logging.getLogger("Plone")

class IHOANeighborhood(form.Schema):
    """Uses IDublinCore
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

    def after_object_added_processor(self, context, event):
        context = self
        all_house_ids = DIVISION_ONE + DIVISION_TWO
        for house_id in all_house_ids:
            div, lot = house_id.split('_')
            house_obj = api.content.create(container=context,
                                           type='hoa_house',
                                           title=house_id,
                                           div=div,
                                           lot=lot)
