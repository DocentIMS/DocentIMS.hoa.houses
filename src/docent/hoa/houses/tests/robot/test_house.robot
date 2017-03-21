# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s docent.hoa.houses -t test_house.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src docent.hoa.houses.testing.DOCENT_HOA_HOUSES_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot src/plonetraining/testing/tests/robot/test_house.robot
#
# See the http://docs.plone.org for further details (search for robot
# framework).
#
# ============================================================================

*** Settings *****************************************************************

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***************************************************************

Scenario: As a site administrator I can add a house
  Given a logged-in site administrator
    and an add house form
   When I type 'My house' into the title field
    and I submit the form
   Then a house with the title 'My house' has been created

Scenario: As a site administrator I can view a house
  Given a logged-in site administrator
    and a house 'My house'
   When I go to the house view
   Then I can see the house title 'My house'


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator

an add house form
  Go To  ${PLONE_URL}/++add++house

a house 'My house'
  Create content  type=house  id=my-house  title=My house


# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.title  ${title}

I submit the form
  Click Button  Save

I go to the house view
  Go To  ${PLONE_URL}/my-house
  Wait until page contains  Site Map


# --- THEN -------------------------------------------------------------------

a house with the title '${title}' has been created
  Wait until page contains  Site Map
  Page should contain  ${title}
  Page should contain  Item created

I can see the house title '${title}'
  Wait until page contains  Site Map
  Page should contain  ${title}
