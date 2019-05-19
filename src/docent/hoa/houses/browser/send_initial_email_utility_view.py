import logging
from AccessControl import Unauthorized

from five import grok

from plone import api
from docent.hoa.houses.content.hoa_annual_inspection import IHOAAnnualInspection
from docent.hoa.houses.content.hoa_house import IHOAHouse
from zope.component import getMultiAdapter
from docent.hoa.houses.app_config import HOME_OWNERS_GID

class View(grok.View):
    grok.context(IHOANeighborhood)
    grok.require("cmf.ManagePortal")
    grok.name('send-initial-email')

    def update(self):
        context = self.context

        current_state =  api.content.get_state(obj=context)

        if current_state != 'draft':
            self.request.response(context.absolute_url())

        if not hasattr(context, 'initial_email_sent'):
            self.request.response(context.absolute_url())

        emails_sent = self.sendInitialNotices(lock=True)

        if emails_sent:
            #do something
            setattr(context, 'initial_email_sent', True)

        self.request.response(context.absolute_url())


    def sendInitialNotices(self, context=context, lock=False):
        if lock:

            portal = api.portal.get()

            house_inspection_title = getattr(self, 'house_inspection_title', None)
            if not house_inspection_title:
                api.portal.show_message(message="We cannot locate the appropriate home inspections. Please verify this "
                                                "inspection was properly configured.",
                                        request=context.REQUEST,
                                        type='warning')
                return False

            secretary_email = getattr(neighborhood_container, 'secretary_email', None)

            home_owners = api.user.get_users(groupname=HOME_OWNERS_GID)
            home_owner_emails = (md.getProperty('email') for md in home_owners if md)

            txt_msg = 'Hello Meadows Residents,\n\nThe %s Annual Property Inspection will be conducted between %s ' \
                      'and %s.\n\nYour home will be inspected sometime during this period. For important information ' \
                      'on the Annual Property Inspection go to our ' \
                      'website.\n\nThanks,\nThe Meadows Board.' % (current_year, start_date, end_date)

            html_msg = '<p>Hello Meadows Residents,</p><p>The %s Annual Property Inspection will be conducted between' \
                       ' %s and %s.</p><p>Your home will be inspected sometime during this period. For important ' \
                       'information on the Annual Property Inspection go to our website.</p><p>Thanks,<br />The ' \
                       'Meadows Board.</p>' % (current_year, start_date, end_date)

            mime_msg = MIMEMultipart('related')
            mime_msg_alt = MIMEMultipart('alternative')

            mime_msg['Subject'] = house_inspection_title
            mime_msg['From'] = secretary_email
            mime_msg['To'] = secretary_email
            mime_msg['Bcc'] = ','.join(list(home_owner_emails))
            mime_msg.preamble = 'This is a multi-part message in MIME format.'
            mime_msg.attach(mime_msg_alt)

            meadows_logo = portal.restrictedTraverse("++resource++docent.hoa.houses/theMeadows.jpeg")
            if meadows_logo:
                msg_image = MIMEImage(meadows_logo.GET())
                msg_image.add_header('Content-ID', '<meadows_logo>')
                mime_msg.attach(msg_image)

            send_message_html = "<html><body><div><div style='width: 100%%; height: 88px;'><div style='float:right'><img src='cid:meadows_logo'></div></div><div>"
            send_message_html += html_msg
            send_message_html += "</div></div></body></html>"

            mime_msg_alt.attach(MIMEText(txt_msg, 'plain'))
            mime_msg_alt.attach(MIMEText(send_message_html, 'html'))

            host = portal.MailHost
            host.send(mime_msg, immediate=True)

            return True
