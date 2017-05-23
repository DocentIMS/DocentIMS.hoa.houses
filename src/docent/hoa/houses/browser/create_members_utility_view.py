import logging
from AccessControl import Unauthorized

from five import grok
import StringIO
import csv
from plone import api
from plone.api.exc import MissingParameterError, InvalidParameterError, UserNotFoundError
from docent.hoa.houses.content.hoa_neighborhood import IHOANeighborhood
from docent.hoa.houses.app_config import HOME_OWNERS_GID

from zope.component import getMultiAdapter

import random
import string

logger = logging.getLogger("Plone")

def random_key(length):
    key = ''
    for i in range(length):
        key += random.choice(string.lowercase + string.uppercase + string.digits)
    return key

class View(grok.View):
    grok.context(IHOANeighborhood)
    grok.require("cmf.ManagePortal")
    grok.name('create-home-owners')

    def render(self):
        return self.createMembersFromCSV()

    def createMembersFromCSV(self):
        """Update all homes tagged in a csv file named: house_block.csv"""
        request = self.request
        context = self.context

        authenticator = getMultiAdapter((context, request), name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized

        if hasattr(context, 'home_owners.csv'):
            home_owners_csv = getattr(context, 'home_owners.csv')
            data = home_owners_csv.file.data
            io = StringIO.StringIO(data)

            reader = csv.reader(io, delimiter=',')
            header = reader.next()

            if header != ['email', 'Fullname']:
                api.portal.show_message(message="Improper Headers for CSV input.",
                                        type='warning',
                                        request=self.REQUEST)
                return

            member_exceptions = []
            group_exceptions = []
            for line in reader:
                email, full_name = line
                properties = dict(fullname=full_name)
                password = random_key(10)
                member = None

                try:
                    member = api.user.create(email=email,
                                             password=password,
                                             properties=properties)
                except MissingParameterError:
                    member_exceptions.append(email)
                except InvalidParameterError:
                    member_exceptions.append(email)
                except AttributeError:
                    member_exceptions.append(email)
                except ValueError:
                    member_exceptions.append(email)

                if member:
                    try:
                        api.group.add_user(groupname=HOME_OWNERS_GID,
                                           user=member)
                    except UserNotFoundError:
                        group_exceptions.append(email)
                    except ValueError:
                        group_exceptions.append(email)

            api.portal.show_message(message="All Members Listed in CSV successfully created. If any member not "
                                            "created a separate notice will display.",
                                    type='info',
                                    request=request)
            if member_exceptions:
                api.portal.show_message(message="Could not create the following members, their "
                                                "accounts may pre-exist: %s" % ', '.join(member_exceptions),
                                        type='warning',
                                        request=request)

            if group_exceptions:
                api.portal.show_message(message="The following members could not be added to the Home "
                                                "Owners group: %s" % ', '.join(group_exceptions),
                                        type='warning',
                                        request=request)
        else:
            api.portal.show_message(message="No Members CSV File Provided",
                                    type='warning',
                                    request=request)

        return request.response.redirect(context.absolute_url())