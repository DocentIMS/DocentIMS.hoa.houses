import logging
from five import grok
from plone import api
from plone.api.exc import MissingParameterError
from plone.protect.utils import addTokenToUrl
from docent.hoa.houses.app_config import HOME_INSPECTION_STATE_TITLES
from docent.hoa.houses.content.hoa_house import IHOAHouse

grok.templatedir('templates')

def getOwnerAndEmailStructureById(member_id):
    if not member_id:
        return ''
    try:
        member_data = api.user.get(userid=member_id)
        fullname = member_data.getProperty('fullname')
        email = member_data.getProperty('email')
    except MissingParameterError:
        return '<em>Unknown Member</em>'

    return "<a href='mailto:%s'>%s</a>" % (email, fullname)

class View(grok.View):
    grok.context(IHOAHouse)
    grok.require("zope2.View")
    grok.template("hoa_house")

    def update(self):
        """
        get email html structure for all home owners and set them as view attribute
        """
        context = self.context
        owner_one = getattr(context, 'owner_one', '')
        self.owner_one = getOwnerAndEmailStructureById(owner_one)
        owner_two = getattr(context, 'owner_two', '')
        self.owner_two = getOwnerAndEmailStructureById(owner_two)
        resident_one = getattr(context, 'resident_one', '')
        self.resident_one = getOwnerAndEmailStructureById(resident_one)
        resident_two = getattr(context, 'resident_two', '')
        self.resident_two = getOwnerAndEmailStructureById(resident_two)
        property_manager = getattr(context, 'property_manager', '')
        self.property_manager = getOwnerAndEmailStructureById(property_manager)

        self.hasOwners = False
        self.hasRenters = False
        self.hasPM = False

        if owner_one or owner_two:
            self.hasOwners = True

        if resident_one or resident_two:
            self.hasRenters = True

        if property_manager:
            self.hasPM = True

        house_inspection_objs = context.listFolderContents(contentFilter={"portal_type":"hoa_house_inspection",
                                                                            "sort_on":"created",
                                                                            "sort_order":"ascending"})

        self.inspections = house_inspection_objs

    def getRentalStatus(self):
        if getattr(self.context, 'rental'):
            return 'Is Rental'
        else:
            return ''

    def getState(self, obj):
        status = api.content.get_state(obj=obj)

        return HOME_INSPECTION_STATE_TITLES.get(status)