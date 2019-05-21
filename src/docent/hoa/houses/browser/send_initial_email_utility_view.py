import logging
from AccessControl import Unauthorized

from five import grok

from plone import api
from docent.hoa.houses.content.hoa_annual_inspection import IHOAAnnualInspection

from docent.hoa.houses.content.hoa_house import IHOAHouse
from zope.component import getMultiAdapter
from docent.hoa.houses.app_config import HOME_OWNERS_GID, PROPERTY_MANAGERS_GID

import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging
logger = logging.getLogger("Plone")

class View(grok.View):
    grok.context(IHOAAnnualInspection)
    grok.require("cmf.ManagePortal")
    grok.name('send-initial-email')

    def render(self):

        return self.sendEmailUtility()

    def sendEmailUtility(self):
        context = self.context

        current_state =  api.content.get_state(obj=context)

        if current_state != 'draft':
            self.request.response.redirect(context.absolute_url())

        if not hasattr(context, 'initial_email_sent'):
            api.portal.show_message(message="Kickoff email has already been sent.",
                                        request=context.REQUEST,
                                        type='warning')

            self.request.response.redirect(context.absolute_url())
        

        emails_sent = self.sendInitialNotices(context=context, lock=True)

        if emails_sent:
            #do something
            setattr(context, 'initial_email_sent', True)

        self.request.response.redirect(context.absolute_url())


    def sendInitialNotices(self, context=None, lock=False):

        if lock:
            portal = api.portal.get()
            inspection_container = context.aq_parent
            house_inspection_title = inspection_container.title
            if not house_inspection_title:
                api.portal.show_message(message="We cannot locate the appropriate home inspections. Please verify this "
                                                "inspection was properly configured.",
                                        request=context.REQUEST,
                                        type='warning')
                return False

            secretary_email = getattr(inspection_container, 'secretary_email', None)

            home_owners = api.user.get_users(groupname=HOME_OWNERS_GID)
            home_owner_emails = {md.getProperty('email') for md in home_owners if md}

            property_managers = api.user.get_users(groupname=PROPERTY_MANAGERS_GID)
            property_manager_emails = {md.getProperty('email') for md in property_managers if md}
            
            emails_to_send = home_owner_emails.union(property_manager_emails)

            current_year = getattr(context, 'start_date').strftime('%Y')
            start_date = getattr(context, 'start_date').strftime('%B %d, %Y')
            end_date = getattr(context, 'end_date').strftime('%B %d, %Y')
            
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

            mime_msg['Subject'] = '%s %s' % (house_inspection_title, current_year)
            mime_msg['From'] = secretary_email
            mime_msg['To'] = secretary_email
            #mime_msg['Bcc'] = ','.join(list(emails_to_send))
            lmsg = ','.join(list(home_owner_emails))
            logger.info('I would have sent to: %s' % lmsg)
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
