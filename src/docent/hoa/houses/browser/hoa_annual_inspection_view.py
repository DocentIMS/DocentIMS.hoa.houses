import logging
from five import grok
from plone import api
from plone.api.exc import MissingParameterError
from plone.protect.utils import addTokenToUrl
from docent.hoa.houses.app_config import HOME_INSPECTION_STATE_TITLES
from docent.hoa.houses.content.hoa_house import IHOAHouse
from docent.hoa.houses.content.hoa_house_inspection import IHOAHouseInspection
from docent.hoa.houses.content.hoa_annual_inspection import IHOAAnnualInspection

grok.templatedir('templates')

def getWalkerAndEmailStructureById(member_id):
    if not member_id:
        return ''
    fullname = ''
    email = ''
    try:
        member_data = api.user.get(userid=member_id)
        if not member_data:
            current_member = api.user.get_current()
            if 'Manager' in api.user.get_roles(user=current_member):
                return '<em>Unknown Member</em> - %s' % member_id
            else:
                return '<em>Unknown Member</em>'
        fullname = member_data.getProperty('fullname')
        email = member_data.getProperty('email')
    except MissingParameterError:
        current_member = api.user.get_current()
        if 'Manager' in api.user.get_roles(user=current_member):
            return '<em>Unknown Member</em> - %s' % member_id
        else:
            return '<em>Unknown Member</em>'

    if not fullname and not email:
        return member_id

    return "<a href='mailto:%s'>%s</a>" % (email, fullname)

def getRowStructureForEmailReports(context, report_dict):
    if not report_dict:
        return ['<td></td><td></td><td></td>']

    parent_container = context.aq_parent
    #get_address()
    row_cells = []
    for house_id in sorted(report_dict.keys()):
        structure = ''
        house_obj = getattr(parent_container, house_id, None)
        if house_obj:
            house_address = house_obj.get_address()
            house_url = house_obj.absolute_url()
            structure += "<td>%s</td><td><a href='%s'>%s</a></td>" % (house_address, house_url, house_id)
        else:
            structure += "<td></td><td>%s</td>" % house_id

        member_ids = report_dict.get(house_id)
        if member_ids:
            structure += "<td>%s" % getWalkerAndEmailStructureById(member_ids[0])
            for member_id in member_ids[1:]:
                structure += ", %s" % getWalkerAndEmailStructureById(member_id)
            structure += "</td>"
        else:
            structure += "<td></td>"

        row_cells.append(structure)

    return row_cells

class View(grok.View):
    grok.context(IHOAAnnualInspection)
    grok.require("zope2.View")
    grok.template("hoa_annual_inspection")

    def update(self):
        """
        get email html structure for all home owners and set them as view attribute
        """
        context = self.context
        self.group_a_member_one = getWalkerAndEmailStructureById(getattr(context, 'group_a_member_one', ''))
        self.group_a_member_two = getWalkerAndEmailStructureById(getattr(context, 'group_a_member_two', ''))
        self.group_b_member_one = getWalkerAndEmailStructureById(getattr(context, 'group_b_member_one', ''))
        self.group_b_member_two = getWalkerAndEmailStructureById(getattr(context, 'group_b_member_two', ''))
        self.group_c_member_one = getWalkerAndEmailStructureById(getattr(context, 'group_c_member_one', ''))
        self.group_c_member_two = getWalkerAndEmailStructureById(getattr(context, 'group_c_member_two', ''))
        self.group_d_member_one = getWalkerAndEmailStructureById(getattr(context, 'group_d_member_one', ''))
        self.group_d_member_two = getWalkerAndEmailStructureById(getattr(context, 'group_d_member_two', ''))
        self.group_e_member_one = getWalkerAndEmailStructureById(getattr(context, 'group_e_member_one', ''))
        self.group_e_member_two = getWalkerAndEmailStructureById(getattr(context, 'group_e_member_two', ''))

        # pic_req = 'No'
        # if getattr(context, 'pic_req'):
        #     pic_req = "Yes"

        # self.pic_req = pic_req

        self.team_a = False
        if self.group_a_member_one or self.group_a_member_two:
            self.team_a = True
        self.team_b = False
        if self.group_b_member_one or self.group_b_member_two:
            self.team_b = True
        self.team_c = False
        if self.group_c_member_one or self.group_c_member_two:
            self.team_c = True
        self.team_d = False
        if self.group_d_member_one or self.group_d_member_two:
            self.team_d = True
        self.team_e = False
        if self.group_e_member_one or self.group_e_member_two:
            self.team_e = True

        self.house_failure_log_structure = getRowStructureForEmailReports(context, getattr(context, 'house_failure_log'))
        self.house_pass_log_structure = getRowStructureForEmailReports(context, getattr(context, 'house_pass_log'))
        self.rewalk_failure_log_structure = getRowStructureForEmailReports(context, getattr(context, 'rewalk_failure_log'))
        self.rewalk_pass_log_structure = getRowStructureForEmailReports(context, getattr(context, 'rewalk_pass_log'))
