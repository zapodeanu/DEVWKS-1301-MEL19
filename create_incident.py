
# developed by Gabi Zapodeanu, TSA, Global Partner Organization


import requests
import json
import logging

from config import SNOW_URL, SNOW_USER, SNOW_PASS

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # Disable insecure https warnings


def get_user_sys_id(username):

    # find the ServiceNow user_id for the specified user

    url = SNOW_URL + '/table/sys_user?sysparm_limit=1&name=' + username
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.get(url, auth=(SNOW_USER, SNOW_PASS), headers=headers)
    user_json = response.json()
    return user_json['result'][0]['sys_id']


def create_incident(description, comment, username, severity):

    # This function will create a new incident with the {description}, {comments}, severity for the {user}

    caller_sys_id = get_user_sys_id(username)
    print('\nAPIUSER ServiceNow sysid is: ' + caller_sys_id)
    url = SNOW_URL + '/table/incident'
    payload = {'short_description': description,
               'comments': (comment + ', \nIncident created using APIs by caller ' + username),
               'caller_id': caller_sys_id,
               'urgency': severity
               }
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    logging.debug('Create new incident')
    response = requests.post(url, auth=(SNOW_USER, SNOW_PASS), data=json.dumps(payload), headers=headers)
    print('\nServiceNow REST API call response: ' + str(response.status_code))
    incident_json = response.json()
    incident_number = incident_json['result']['number']
    logging.debug('Incident created: ' + incident_number)
    return incident_number


# main application

logging.basicConfig(
    filename='application_run.log',
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

print('Your name is : ')
user_name = raw_input()

comments = ('The user with the name: ' + str(user_name) + ' created this test incident using APIs')
incident = create_incident('User Notification - ' + str(user_name), comments, SNOW_USER, 3)

print('Created ServiceNow Incident with the number: ', str(incident))

print('\nEnd Application Run')
