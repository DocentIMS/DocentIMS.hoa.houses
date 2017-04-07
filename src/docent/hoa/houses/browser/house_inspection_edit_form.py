
# -*- coding: utf-8 -*-
from plone.dexterity.events import EditBegunEvent
from plone.dexterity.interfaces import IDexterityEditForm
from plone.dexterity.interfaces import IDexterityFTI

from plone.z3cform import layout

from zope.component import getUtility
from zope.event import notify
from zope.interface import classImplements
from plone import api
from plone.dexterity.browser import edit
from plone.z3cform.fieldsets.utils import remove
from zope.event import notify
from z3c.form import interfaces
from z3c.form import field
from z3c.form.browser.radio import RadioFieldWidget
from plone.directives import form

from docent.hoa.houses import _

inspection_keys_to_fieldset_dict = {'flowerpots_text': 'flowerpots',
                                    'paint_text': 'paint',
                                    'sidewalk_drive_text': 'sidewalk_drive',
                                    'steps_text': 'steps',
                                    'decks_patio_text': 'decks_patio',
                                    'general_maintenance_text': 'general_maintenance'}

class IEmptySchema(form.Schema):
    """
    Empty Schema
    """

class HouseInspectionEditForm(edit.DefaultEditForm):

    def updateWidgets(self):
        super(HouseInspectionEditForm, self).updateWidgets()
        # hidden_fields = ['title',
        #                  'inspection_datetime',
        #                  'passed_datetime',
        #                  'inspected_by_first',
        #                  'inspected_by_second']
        # import pdb;pdb.set_trace()
        # for h_f in hidden_fields:
        #     remove(self, h_f)

        context = self.context
        current_state = api.content.get_state(obj=context)

        if current_state in ['failed_final', 'remedied']:
            for_show = []
            groups = self.groups
            fieldset_dict = {}
            [fieldset_dict.update({group.__name__:group}) for group in groups]

            for key in inspection_keys_to_fieldset_dict.keys():
                if getattr(context, key):
                    for_show.append(key)

            new_schema = field.Fields(IEmptySchema)
            new_groups = []
            for skey in for_show:
                fieldset_key = inspection_keys_to_fieldset_dict.get(skey)
                s_group = fieldset_dict.get(fieldset_key)
                #import pdb;pdb.set_trace()

                s_group.fields['%s_second_image' % fieldset_key].mode = None
                s_group.fields['%s_cond_remains' % fieldset_key].mode = None
                s_group.fields['%s_cond_remains' % fieldset_key].widgetFactory = RadioFieldWidget
                s_group.fields['%s_image' % fieldset_key].mode = interfaces.DISPLAY_MODE
                #s_group.fields['%s_second_image' % fieldset_key].mode = interfaces.HIDDEN_MODE
                #s_group.fields['%s_second_image' % fieldset_key].mode = None
                #new_schema += s_group.fields
                new_groups.append(s_group)

            self.groups = new_groups
        else:
            groups = self.groups
            for group in groups:
                g_name = group.__name__
                if getattr(context, '%s_second_image' % g_name, None):
                    group.fields['%s_second_image' % g_name].mode = interfaces.DISPLAY_MODE


    @property
    def fti(self):
        return getUtility(IDexterityFTI, name=self.portal_type)

    @property
    def label(self):
        type_name = self.fti.Title()
        return _(u"${name} - Failures", mapping={'name': type_name})

DefaultEditView = layout.wrap_form(HouseInspectionEditForm)
classImplements(DefaultEditView, IDexterityEditForm)