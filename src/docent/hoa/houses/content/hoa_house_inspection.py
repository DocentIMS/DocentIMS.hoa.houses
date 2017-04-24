import logging
from datetime import date, datetime
from plone import api
from plone.dexterity.content import Container
from plone.directives import form
from plone.indexer import indexer
from plone.namedfile.field import NamedBlobImage
from plone.supermodel.directives import fieldset
from zope import schema

from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from z3c.form.browser.radio import RadioFieldWidget


from zope.interface import provider, invariant, Invalid
from zope.schema.interfaces import IContextAwareDefaultFactory



from docent.hoa.houses.registry import IHOAHomeLookupRegistry
from docent.hoa.houses.app_config import HOME_ROLE_TO_ATTRIBUTE_LOOKUP_DICT
from docent.hoa.houses.registry import (addHomeToLookupRegistry,
                                        removeHomeFromLookupRegistry,
                                        clearAllHomesForMember,
                                        addCurrentHomeRoles)

from docent.hoa.houses import _

logger = logging.getLogger("Plone")

def getAnnualInspection():
    portal = api.portal.get()
    from docent.hoa.houses.content.hoa_annual_inspection import IHOAAnnualInspection
    annual_inspection_brains = portal.portal_catalog.searchResults(
                                               object_provides=IHOAAnnualInspection.__identifier__,
                                               sort_on="created",
                                               sort_order="descending")
    annual_inspection_brain = None
    if annual_inspection_brains:
        annual_inspection_brain = annual_inspection_brains[0]

    return annual_inspection_brain

def computeTitle():
    today = date.today()
    house_inspection_title = today.strftime(u'%Y-%m')
    return u'House Inspection %s' % house_inspection_title,


REQUIRED_ACTION_VOCABULARY = SimpleVocabulary(
    [SimpleTerm(value='clean', title=_(u'Clean')),
     SimpleTerm(value='repair', title=_(u'Repair')),
     SimpleTerm(value='replace', title=_(u'Replace'))]
    )

IHOAHOUSEINSPECTION_FIELDSETS = ['roof',
                                 'gutters',
                                 'exterior_paint',
                                 'decks',
                                 'entry_way',
                                 'paved_surfaces',
                                 'landscaping',
                                 'general_maintenance' ]

class IHOAHouseInspection(form.Schema):
    """
    """
    fieldset('roof',
        label=u'Roof',
        description=u'',
        fields=['title',
                'inspection_datetime',
                'passed_datetime',
                'inspected_by_first',
                'inspected_by_second',
                'roof_cond_remains',
                'roof_action_required',
                'roof_text',
                'roof_rewalk_text',
                'roof_image',
                'roof_rewalk_image']
    )

    form.mode(title='hidden')
    title = schema.TextLine(
        title=_(u"Title"),
    )

    form.mode(inspection_datetime='hidden')
    inspection_datetime = schema.Datetime(
        title=_(u'First Inspection Datetime'),
        description=_(u''),
        required=False,
    )

    form.mode(passed_datetime='hidden')
    passed_datetime = schema.Datetime(
        title=_(u'Secondary Inspection Datetime'),
        description=_(u''),
        required=False,
    )

    form.mode(inspected_by_first='hidden')
    inspected_by_first = schema.TextLine(
        title=_(u"Primary Inspection By"),
        required=False,
    )

    form.mode(inspected_by_second='hidden')
    inspected_by_second = schema.TextLine(
        title=_(u"Secondary Inspection By"),
        required=False,
    )

    form.mode(roof_cond_remains='hidden')
    form.widget(roof_cond_remains=RadioFieldWidget)
    roof_cond_remains = schema.Choice(
        title=_(u'Roof Condition Remains?'),
        description=_(u''),
        source=SimpleVocabulary([SimpleTerm(value=True,
                                            title=u"Yes"),
                                 SimpleTerm(value=False,
                                            title=U"No")]),
        required=False,
    )

    roof_action_required = schema.Choice(
        title=_(u'Roof Required Action'),
        description=_(u''),
        vocabulary=REQUIRED_ACTION_VOCABULARY,
        required=False,
    )

    roof_text = schema.Text(
        title=_(u"Roof Issue"),
        description=_(u""),
        required=False,
    )

    form.mode(roof_rewalk_text='hidden')
    roof_rewalk_text = schema.Text(
        title=_(u"Roof Issue"),
        description=_(u""),
        required=False,
    )

    roof_image = NamedBlobImage(
        title=_(u"Roof Photo"),
        description=_(u""),
        required=False,
    )

    form.mode(roof_rewalk_image='hidden')
    roof_rewalk_image = NamedBlobImage(
        title=_(u"Roof Re-walk Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('gutters',
        label=u'Gutters',
        description=u'',
        fields=['gutters_cond_remains',
                'gutters_action_required',
                'gutters_text',
                'gutters_rewalk_text',
                'gutters_image',
                'gutters_rewalk_image']
    )

    form.mode(gutters_cond_remains='hidden')
    form.widget(gutters_cond_remains=RadioFieldWidget)
    gutters_cond_remains = schema.Choice(
        title=_(u'Gutter Condition Remains?'),
        description=_(u''),
        source=SimpleVocabulary([SimpleTerm(value=True,
                                            title=u"Yes"),
                                 SimpleTerm(value=False,
                                            title=U"No")]),
        required=False,
    )

    gutters_action_required = schema.Choice(
        title=_(u'Gutters Required Action'),
        description=_(u''),
        vocabulary=REQUIRED_ACTION_VOCABULARY,
        required=False,
    )

    gutters_text = schema.Text(
        title=_(u"Gutters Issue"),
        description=_(u""),
        required=False,
    )

    form.mode(gutters_rewalk_text='hidden')
    gutters_rewalk_text = schema.Text(
        title=_(u"Gutters Issue"),
        description=_(u""),
        required=False,
    )

    gutters_image = NamedBlobImage(
        title=_(u"Gutters Photo"),
        description=_(u""),
        required=False,
    )

    form.mode(gutters_rewalk_image='hidden')
    gutters_rewalk_image = NamedBlobImage(
        title=_(u"Gutters Re-walk Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('exterior_paint',
        label=u'Exterior Paint',
        description=u'',
        fields=['exterior_paint_cond_remains',
                'exterior_paint_action_required',
                'exterior_paint_text',
                'exterior_paint_rewalk_text',
                'exterior_paint_image',
                'exterior_paint_rewalk_image']
    )

    form.mode(exterior_paint_cond_remains='hidden')
    form.widget(exterior_paint_cond_remains=RadioFieldWidget)
    exterior_paint_cond_remains = schema.Choice(
        title=_(u'Exterior Paint Condition Remains?'),
        description=_(u''),
        source=SimpleVocabulary([SimpleTerm(value=True,
                                            title=u"Yes"),
                                 SimpleTerm(value=False,
                                            title=U"No")]),
        required=False,
    )

    exterior_paint_action_required = schema.Choice(
        title=_(u'Exterior Paint Required Action'),
        description=_(u''),
        vocabulary=REQUIRED_ACTION_VOCABULARY,
        required=False,
    )

    exterior_paint_text = schema.Text(
        title=_(u"Exterior Paint Issue"),
        description=_(u""),
        required=False,
    )

    form.mode(exterior_paint_rewalk_text='hidden')
    exterior_paint_rewalk_text = schema.Text(
        title=_(u"Exterior Paint Issue"),
        description=_(u""),
        required=False,
    )

    exterior_paint_image = NamedBlobImage(
        title=_(u"Exterior Paint Photo"),
        description=_(u""),
        required=False,
    )

    form.mode(exterior_paint_rewalk_image='hidden')
    exterior_paint_rewalk_image = NamedBlobImage(
        title=_(u"Exterior Paint Re-walk Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('decks',
        label=u'Decks',
        description=u'',
        fields=['decks_cond_remains',
                'decks_action_required',
                'decks_text',
                'decks_rewalk_text',
                'decks_image',
                'decks_rewalk_image']
    )

    form.mode(decks_cond_remains='hidden')
    form.widget(decks_cond_remains=RadioFieldWidget)
    decks_cond_remains = schema.Choice(
        title=_(u'Decks Condition Remains?'),
        description=_(u''),
        source=SimpleVocabulary([SimpleTerm(value=True,
                                            title=u"Yes"),
                                 SimpleTerm(value=False,
                                            title=U"No")]),
        required=False,
    )

    decks_action_required = schema.Choice(
        title=_(u'Decks Required Action'),
        description=_(u''),
        vocabulary=REQUIRED_ACTION_VOCABULARY,
        required=False,
    )

    decks_text = schema.Text(
        title=_(u"Decks Issue"),
        description=_(u""),
        required=False,
    )

    form.mode(decks_rewalk_text='hidden')
    decks_rewalk_text = schema.Text(
        title=_(u"Decks Issue"),
        description=_(u""),
        required=False,
    )

    decks_image = NamedBlobImage(
        title=_(u"Decks Photo"),
        description=_(u""),
        required=False,
    )

    form.mode(decks_rewalk_image='hidden')
    decks_rewalk_image = NamedBlobImage(
        title=_(u"Decks Re-walk Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('entry_way',
        label=u'Entry Way',
        description=u'',
        fields=['entry_way_cond_remains',
                'entry_way_action_required',
                'entry_way_text',
                'entry_way_rewalk_text',
                'entry_way_image',
                'entry_way_rewalk_image']
    )

    form.mode(entry_way_cond_remains='hidden')
    form.widget(entry_way_cond_remains=RadioFieldWidget)
    entry_way_cond_remains = schema.Choice(
        title=_(u'Entry Way Condition Remains?'),
        description=_(u''),
        source=SimpleVocabulary([SimpleTerm(value=True,
                                            title=u"Yes"),
                                 SimpleTerm(value=False,
                                            title=U"No")]),
        required=False,
    )

    entry_way_action_required = schema.Choice(
        title=_(u'Entry Way Required Action'),
        description=_(u''),
        vocabulary=REQUIRED_ACTION_VOCABULARY,
        required=False,
    )

    entry_way_text = schema.Text(
        title=_(u"Entry Way Issue"),
        description=_(u""),
        required=False,
    )

    form.mode(entry_way_rewalk_text='hidden')
    entry_way_rewalk_text = schema.Text(
        title=_(u"Entry Way Issue"),
        description=_(u""),
        required=False,
    )

    entry_way_image = NamedBlobImage(
        title=_(u"Entry Way Photo"),
        description=_(u""),
        required=False,
    )

    form.mode(entry_way_rewalk_image='hidden')
    entry_way_rewalk_image = NamedBlobImage(
        title=_(u"Entry Way Re-walk Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('paved_surfaces',
        label=u'Paved Surfaces',
        description=u'',
        fields=['paved_surfaces_cond_remains',
                'paved_surfaces_action_required',
                'paved_surfaces_text',
                'paved_surfaces_rewalk_text',
                'paved_surfaces_image',
                'paved_surfaces_rewalk_image']
    )

    form.mode(paved_surfaces_cond_remains='hidden')
    form.widget(paved_surfaces_cond_remains=RadioFieldWidget)
    paved_surfaces_cond_remains = schema.Choice(
        title=_(u'Paved Surfaces Condition Remains?'),
        description=_(u''),
        source=SimpleVocabulary([SimpleTerm(value=True,
                                            title=u"Yes"),
                                 SimpleTerm(value=False,
                                            title=U"No")]),
        required=False,
    )

    paved_surfaces_action_required = schema.Choice(
        title=_(u'Paved Surfaces Required Action'),
        description=_(u''),
        vocabulary=REQUIRED_ACTION_VOCABULARY,
        required=False,
    )

    paved_surfaces_text = schema.Text(
        title=_(u"Paved Surfaces Issue"),
        description=_(u""),
        required=False,
    )

    form.mode(paved_surfaces_rewalk_text='hidden')
    paved_surfaces_rewalk_text = schema.Text(
        title=_(u"Paved Surfaces Issue"),
        description=_(u""),
        required=False,
    )

    paved_surfaces_image = NamedBlobImage(
        title=_(u"Paved Surfaces Photo"),
        description=_(u""),
        required=False,
    )

    form.mode(paved_surfaces_rewalk_image='hidden')
    paved_surfaces_rewalk_image = NamedBlobImage(
        title=_(u"Paved Surfaces Re-walk Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('landscaping',
        label=u'Landscaping',
        description=u'',
        fields=['landscaping_cond_remains',
                'landscaping_action_required',
                'landscaping_text',
                'landscaping_rewalk_text',
                'landscaping_image',
                'landscaping_rewalk_image']
    )

    form.mode(landscaping_cond_remains='hidden')
    form.widget(landscaping_cond_remains=RadioFieldWidget)
    landscaping_cond_remains = schema.Choice(
        title=_(u'Landscaping Condition Remains?'),
        description=_(u''),
        source=SimpleVocabulary([SimpleTerm(value=True,
                                            title=u"Yes"),
                                 SimpleTerm(value=False,
                                            title=U"No")]),
        required=False,
    )

    landscaping_action_required = schema.Choice(
        title=_(u'Landscaping Required Action'),
        description=_(u''),
        vocabulary=REQUIRED_ACTION_VOCABULARY,
        required=False,
    )

    landscaping_text = schema.Text(
        title=_(u"Landscaping Issue"),
        description=_(u""),
        required=False,
    )

    form.mode(landscaping_rewalk_text='hidden')
    landscaping_rewalk_text = schema.Text(
        title=_(u"Landscaping Issue"),
        description=_(u""),
        required=False,
    )

    landscaping_image = NamedBlobImage(
        title=_(u"Landscaping Photo"),
        description=_(u""),
        required=False,
    )

    form.mode(landscaping_rewalk_image='hidden')
    landscaping_rewalk_image = NamedBlobImage(
        title=_(u"Landscaping Re-walk Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('general_maintenance',
        label=u'General Maintenance',
        description=u'',
        fields=['general_maintenance_cond_remains',
                'general_maintenance_action_required',
                'general_maintenance_text',
                'general_maintenance_rewalk_text',
                'general_maintenance_image',
                'general_maintenance_rewalk_image']
    )

    form.mode(general_maintenance_cond_remains='hidden')
    form.widget(general_maintenance_cond_remains=RadioFieldWidget)
    general_maintenance_cond_remains = schema.Choice(
        title=_(u'General Maintenance Condition Remains?'),
        description=_(u''),
        source=SimpleVocabulary([SimpleTerm(value=True,
                                            title=u"Yes"),
                                 SimpleTerm(value=False,
                                            title=U"No")]),
        required=False,
    )

    general_maintenance_action_required = schema.Choice(
        title=_(u'General Maintenance Required Action'),
        description=_(u''),
        vocabulary=REQUIRED_ACTION_VOCABULARY,
        required=False,
    )

    general_maintenance_text = schema.Text(
        title=_(u"General Maintenance Issue"),
        description=_(u""),
        required=False,
    )

    form.mode(general_maintenance_rewalk_text='hidden')
    general_maintenance_rewalk_text = schema.Text(
        title=_(u"General Maintenance Issue"),
        description=_(u""),
        required=False,
    )

    general_maintenance_image = NamedBlobImage(
        title=_(u"General Maintenance Photo"),
        description=_(u""),
        required=False,
    )

    form.mode(general_maintenance_rewalk_image='hidden')
    general_maintenance_rewalk_image = NamedBlobImage(
        title=_(u"General Maintenance Re-walk Photo"),
        description=_(u""),
        required=False,
    )

    # fieldset('flowerpots',
    #     label=u'Flowerpots',
    #     description=u'',
    #     fields=['title',
    #             'inspection_datetime',
    #             'passed_datetime',
    #             'inspected_by_first',
    #             'inspected_by_second',
    #             'flowerpots_cond_remains',
    #             'flowerpots_text',
    #             'flowerpots_image',
    #             'flowerpots_second_image']
    # )
    #
    # # flowerpots_bool = schema.Bool(
    # #     title=_(u'Flowerpots Fail'),
    # #     description=_(u''),
    # #     required=False,
    # # )
    #
    # form.mode(title='hidden')
    # title = schema.TextLine(
    #     title=_(u"Title"),
    # )
    #
    # form.mode(inspection_datetime='hidden')
    # inspection_datetime = schema.Datetime(
    #     title=_(u'First Inspection Datetime'),
    #     description=_(u''),
    #     required=False,
    # )
    #
    # form.mode(passed_datetime='hidden')
    # passed_datetime = schema.Datetime(
    #     title=_(u'Secondary Inspection Datetime'),
    #     description=_(u''),
    #     required=False,
    # )
    #
    # form.mode(inspected_by_first='hidden')
    # inspected_by_first = schema.TextLine(
    #     title=_(u"Primary Inspection By"),
    #     required=False,
    # )
    #
    # form.mode(inspected_by_second='hidden')
    # inspected_by_second = schema.TextLine(
    #     title=_(u"Secondary Inspection By"),
    #     required=False,
    # )
    #
    # form.mode(flowerpots_cond_remains='hidden')
    # form.widget(flowerpots_cond_remains=RadioFieldWidget)
    # flowerpots_cond_remains = schema.Choice(
    #     title=_(u'Flowerpot Condition Remains?'),
    #     description=_(u''),
    #     source=SimpleVocabulary([SimpleTerm(value=True,
    #                                         title=u"Yes"),
    #                              SimpleTerm(value=False,
    #                                         title=U"No")]),
    #     required=False,
    # )
    #
    # flowerpots_text = schema.Text(
    #     title=_(u"Flowerpots Issue"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # flowerpots_image = NamedBlobImage(
    #     title=_(u"Flowerpots Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # form.mode(flowerpots_second_image='hidden')
    # flowerpots_second_image = NamedBlobImage(
    #     title=_(u"Flowerpots Re-walk Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # fieldset('paint',
    #     label=u'Paint',
    #     description=u'',
    #     fields=['paint_cond_remains',
    #             'paint_text',
    #             'paint_image',
    #             'paint_second_image']
    # )
    #
    # # paint_bool = schema.Bool(
    # #     title=_(u'Paint Fail'),
    # #     description=_(u''),
    # #     required=False,
    # # )
    #
    # form.mode(paint_cond_remains='hidden')
    # form.widget(paint_cond_remains=RadioFieldWidget)
    # paint_cond_remains = schema.Choice(
    #     title=_(u'Paint Condition Remains?'),
    #     description=_(u''),
    #     source=SimpleVocabulary([SimpleTerm(value=True,
    #                                         title=u"Yes"),
    #                              SimpleTerm(value=False,
    #                                         title=U"No")]),
    #     required=False,
    # )
    #
    # paint_text = schema.Text(
    #     title=_(u"Paint Issue"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # paint_image = NamedBlobImage(
    #     title=_(u"Paint Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # form.mode(paint_second_image='hidden')
    # paint_second_image = NamedBlobImage(
    #     title=_(u"Paint Re-walk Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # fieldset('sidewalk_drive',
    #     label=u'Sidewalk/Drive',
    #     description=u'',
    #     fields=['sidewalk_drive_cond_remains',
    #             'sidewalk_drive_text',
    #             'sidewalk_drive_image',
    #             'sidewalk_drive_second_image']
    # )
    #
    # # sidewalk_drive_bool = schema.Bool(
    # #     title=_(u'Sidewalk/Drive Fail'),
    # #     description=_(u''),
    # #     required=False,
    # # )
    #
    # form.mode(sidewalk_drive_cond_remains='hidden')
    # form.widget(sidewalk_drive_cond_remains=RadioFieldWidget)
    # sidewalk_drive_cond_remains = schema.Choice(
    #     title=_(u'Sidewalk/Drive Condition Remains?'),
    #     description=_(u''),
    #     source=SimpleVocabulary([SimpleTerm(value=True,
    #                                         title=u"Yes"),
    #                              SimpleTerm(value=False,
    #                                         title=U"No")]),
    #     required=False,
    # )
    #
    # sidewalk_drive_text = schema.Text(
    #     title=_(u"Sidewalk/Drive Issue"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # sidewalk_drive_image = NamedBlobImage(
    #     title=_(u"Sidewalk/Drive Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # form.mode(sidewalk_drive_second_image='hidden')
    # sidewalk_drive_second_image = NamedBlobImage(
    #     title=_(u"Sidewalk/Drive Re-walk Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # fieldset('steps',
    #     label=u'Steps',
    #     description=u'',
    #     fields=['steps_cond_remains',
    #             'steps_text',
    #             'steps_image',
    #             'steps_second_image']
    # )
    #
    # # steps_bool = schema.Bool(
    # #     title=_(u'Steps Fail'),
    # #     description=_(u''),
    # #     required=False,
    # # )
    #
    # form.mode(steps_cond_remains='hidden')
    # form.widget(steps_cond_remains=RadioFieldWidget)
    # steps_cond_remains = schema.Choice(
    #     title=_(u'Steps Condition Remains?'),
    #     description=_(u''),
    #     source=SimpleVocabulary([SimpleTerm(value=True,
    #                                         title=u"Yes"),
    #                              SimpleTerm(value=False,
    #                                         title=U"No")]),
    #     required=False,
    # )
    #
    # steps_text = schema.Text(
    #     title=_(u"Steps Issue"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # steps_image = NamedBlobImage(
    #     title=_(u"Steps Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # form.mode(steps_second_image='hidden')
    # steps_second_image = NamedBlobImage(
    #     title=_(u"Steps Re-walk Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # fieldset('decks_patio',
    #     label=u'Decks/Patio',
    #     description=u'',
    #     fields=['decks_patio_cond_remains',
    #             'decks_patio_text',
    #             'decks_patio_image',
    #             'decks_patio_second_image']
    # )
    #
    # # decks_patio_bool = schema.Bool(
    # #     title=_(u'Decks/Patio Fail'),
    # #     description=_(u''),
    # #     required=False,
    # # )
    #
    # form.mode(decks_patio_cond_remains='hidden')
    # form.widget(decks_patio_cond_remains=RadioFieldWidget)
    # decks_patio_cond_remains = schema.Choice(
    #     title=_(u'Decks/Patio Condition Remains?'),
    #     description=_(u''),
    #     source=SimpleVocabulary([SimpleTerm(value=True,
    #                                         title=u"Yes"),
    #                              SimpleTerm(value=False,
    #                                         title=U"No")]),
    #     required=False,
    # )
    #
    # decks_patio_text = schema.Text(
    #     title=_(u"Decks/Patio Issue"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # decks_patio_image = NamedBlobImage(
    #     title=_(u"Decks/Patio Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # form.mode(decks_patio_second_image='hidden')
    # decks_patio_second_image = NamedBlobImage(
    #     title=_(u"Decks/Patio Re-walk Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # fieldset('general_maintenance',
    #     label=u'General Maintenance',
    #     description=u'',
    #     fields=['general_maintenance_cond_remains',
    #             'general_maintenance_text',
    #             'general_maintenance_image',
    #             'general_maintenance_second_image']
    # )
    #
    # # general_maintenance_bool = schema.Bool(
    # #     title=_(u'General Maintenance Fail'),
    # #     description=_(u''),
    # #     required=False,
    # # )
    #
    # form.mode(general_maintenance_cond_remains='hidden')
    # form.widget(general_maintenance_cond_remains=RadioFieldWidget)
    # general_maintenance_cond_remains = schema.Choice(
    #     title=_(u'General Maintenance Condition Remains?'),
    #     description=_(u''),
    #     source=SimpleVocabulary([SimpleTerm(value=True,
    #                                         title=u"Yes"),
    #                              SimpleTerm(value=False,
    #                                         title=U"No")]),
    #     required=False,
    # )
    #
    # general_maintenance_text = schema.Text(
    #     title=_(u"General Maintenance Issue"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # general_maintenance_image = NamedBlobImage(
    #     title=_(u"General Maintenance Photo"),
    #     description=_(u""),
    #     required=False,
    # )
    #
    # form.mode(general_maintenance_second_image='hidden')
    # general_maintenance_second_image = NamedBlobImage(
    #     title=_(u"General Maintenance Re-walk Photo"),
    #     description=_(u""),
    #     required=False,
    # )

    @invariant
    def confirmAction(data):
        context = data.__context__
        context_state = api.content.get_state(obj=context)
        for fieldset_id in IHOAHOUSEINSPECTION_FIELDSETS:
            if hasattr(data, '%s_text' % fieldset_id):
                if getattr(data, '%s_text' % fieldset_id):
                    action_required = getattr(data, '%s_action_required' % fieldset_id)
                    if not action_required:
                        error_keys = fieldset_id.split('_')
                        error_str = ' '.join(error_keys)
                        raise Invalid(_(u"You must provide a required action for %s." % error_str))
            if hasattr(data, '%s_action_required' % fieldset_id):
                if getattr(data, '%s_action_required' % fieldset_id):
                    failure_text = getattr(data, '%s_text' % fieldset_id)
                    if not failure_text:
                        error_keys = fieldset_id.split('_')
                        error_str = ' '.join(error_keys)
                        raise Invalid(_(u"You must provide a description of the issue if action is required for: %s." % error_str))

    @invariant
    def conditionPerists(data):
        context = data.__context__
        context_state = api.content.get_state(obj=context)
        if context_state in ['failed_final', 'remedied']:
            for fieldset_id in IHOAHOUSEINSPECTION_FIELDSETS:
                if hasattr(data, '%s_cond_remains' % fieldset_id):
                    if getattr(data, '%s_cond_remains' % fieldset_id):
                        rewalk_txt = getattr(data, '%s_rewalk_text' % fieldset_id)
                        rewalk_image = getattr(data, '%s_rewalk_image' % fieldset_id)
                        if not rewalk_txt:
                            error_keys = fieldset_id.split('_')
                            error_str = ' '.join(error_keys)
                            raise Invalid(_(u"You must provide an a reason the condition persists for %s." % error_str))
                        if not rewalk_image:
                            error_keys = fieldset_id.split('_')
                            error_str = ' '.join(error_keys)
                            raise Invalid(_(u"You must provide an a photo of the condition for %s." % error_str))

    @invariant
    def imagesRequired(data):
        # active_annual_inspection = getAnnualInspection()
        # if not active_annual_inspection:
        #     return
        # aai_obj = active_annual_inspection.getObject()
        # pic_req = getattr(aai_obj, 'pic_req', False)
        # if pic_req:
        #     for fieldset_id in ['flowerpots', 'paint', 'sidewalk_drive', 'steps', 'decks_patio', 'general_maintenance']:
        #         if getattr(data, '%s_text' % fieldset_id):
        #             image = getattr(data, '%s_image' % fieldset_id)
        #             if not image:
        #                 error_keys = fieldset_id.split('_')
        #                 error_str = ' '.join(error_keys)
        #                 raise Invalid(_(u"You must provide an image for %s." % error_str))
        context = data.__context__
        context_state = api.content.get_state(obj=context)

        for fieldset_id in IHOAHOUSEINSPECTION_FIELDSETS:
            if context_state == 'failed_initial':
                if getattr(data, '%s_text' % fieldset_id):
                    image = getattr(data, '%s_image' % fieldset_id)
                    if not image:
                        error_keys = fieldset_id.split('_')
                        error_str = ' '.join(error_keys)
                        raise Invalid(_(u"You must provide an image for %s." % error_str))
            if context_state == 'failed_final':
                if getattr(data, '%s_rewalk_text' % fieldset_id):
                    image = getattr(data, '%s_rewalk_image' % fieldset_id)
                    if not image:
                        error_keys = fieldset_id.split('_')
                        error_str = ' '.join(error_keys)
                        raise Invalid(_(u"You must provide an image for %s." % error_str))

class HOAHouseInspection(Container):
    """
    """

    def after_transition_processor(self):
        context_state = api.content.get_state(obj=self)
        now = datetime.now()
        if context_state == 'passed':
            setattr(self, 'passed_datetime', now)

        setattr(self, 'inspection_datetime', now)
