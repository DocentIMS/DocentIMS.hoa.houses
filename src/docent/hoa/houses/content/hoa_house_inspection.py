import logging
from datetime import date, datetime
from plone import api
from plone.dexterity.content import Container
from plone.directives import form
from plone.indexer import indexer
from plone.namedfile.field import NamedBlobImage
from plone.supermodel.directives import fieldset
from zope import schema
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

def computeTitle():
    today = date.today()
    house_inspection_title = today.strftime(u'%Y-%m')
    return u'House Inspection %s' % house_inspection_title,

class IHOAHouseInspection(form.Schema):
    """
    """
    #form.mode(title='hidden')
    title = schema.TextLine(
        title=_(u"Title"),
    )

    inspection_datetime = schema.Datetime(
        title=_(u'First Inspection Datetime'),
        description=_(u''),
        required=False,
    )

    passed_datetime = schema.Datetime(
        title=_(u'Secondary Inspection Datetime'),
        description=_(u''),
        required=False,
    )

    fieldset('flowerpots',
        label=u'Flowerpots',
        description=u'',
        fields=['flowerpots_bool',
                'flowerpots_text',
                'flowerpots_image']
    )

    flowerpots_bool = schema.Bool(
        title=_(u'Flowerpots Fail'),
        description=_(u''),
        required=False,
    )

    flowerpots_text = schema.Text(
        title=_(u"Flowerpots Issue"),
        description=_(u""),
        required=False,
    )

    flowerpots_image = NamedBlobImage(
        title=_(u"Flowerpots Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('paint',
        label=u'Paint',
        description=u'',
        fields=['paint_bool',
                'paint_text',
                'paint_image']
    )

    paint_bool = schema.Bool(
        title=_(u'Paint Fail'),
        description=_(u''),
        required=False,
    )

    paint_text = schema.Text(
        title=_(u"Paint Issue"),
        description=_(u""),
        required=False,
    )

    paint_image = NamedBlobImage(
        title=_(u"Paint Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('sidewalk_drive',
        label=u'Sidewalk/Drive',
        description=u'',
        fields=['sidewalk_drive_bool',
                'sidewalk_drive_text',
                'sidewalk_drive_image']
    )

    sidewalk_drive_bool = schema.Bool(
        title=_(u'Sidewalk/Drive Fail'),
        description=_(u''),
        required=False,
    )

    sidewalk_drive_text = schema.Text(
        title=_(u"Sidewalk/Drive Issue"),
        description=_(u""),
        required=False,
    )

    sidewalk_drive_image = NamedBlobImage(
        title=_(u"Sidewalk/Drive Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('steps',
        label=u'Steps',
        description=u'',
        fields=['steps_bool',
                'steps_text',
                'steps_image']
    )

    steps_bool = schema.Bool(
        title=_(u'Steps Fail'),
        description=_(u''),
        required=False,
    )

    steps_text = schema.Text(
        title=_(u"Steps Issue"),
        description=_(u""),
        required=False,
    )

    steps_image = NamedBlobImage(
        title=_(u"Steps Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('decks_patio',
        label=u'Decks/Patio',
        description=u'',
        fields=['decks_patio_bool',
                'decks_patio_text',
                'decks_patio_image']
    )

    decks_patio_bool = schema.Bool(
        title=_(u'Decks/Patio Fail'),
        description=_(u''),
        required=False,
    )

    decks_patio_text = schema.Text(
        title=_(u"Decks/Patio Issue"),
        description=_(u""),
        required=False,
    )

    decks_patio_image = NamedBlobImage(
        title=_(u"Decks/Patio Photo"),
        description=_(u""),
        required=False,
    )

    fieldset('general_maintenance',
        label=u'General Maintenance',
        description=u'',
        fields=['general_maintenance_bool',
                'general_maintenance_text',
                'general_maintenance_image']
    )

    general_maintenance_bool = schema.Bool(
        title=_(u'General Maintenance Fail'),
        description=_(u''),
        required=False,
    )

    general_maintenance_text = schema.Text(
        title=_(u"General Maintenance Issue"),
        description=_(u""),
        required=False,
    )

    general_maintenance_image = NamedBlobImage(
        title=_(u"General Maintenance Photo"),
        description=_(u""),
        required=False,
    )


class HOAHouseInspection(Container):
    """
    """

    def after_transition_processor(self):
        context_state = api.content.get_state(obj=self)
        now = datetime.now()
        if context_state == 'passed':
            setattr(self, 'passed_datetime', now)

        setattr(self, 'inspection_datetime', now)
