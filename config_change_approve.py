
# developed by Gabi Zapodeanu, TSA, Global Partner Organization


import cli
import time
import difflib
import requests
import json
import logging

from config import WEBEX_TEAMS_URL, WEBEX_TEAMS_AUTH, WEBEX_TEAMS_SPACE, WEBEX_TEAMS_MEMBER
from config import HOST, USER, PASS
from config import SNOW_URL, SNOW_USER, SNOW_PASS

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.auth import HTTPBasicAuth  # for Basic Auth

from time import sleep
from cli import cli, execute, configure

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # Disable insecure https warnings


ROUTER_AUTH = HTTPBasicAuth(USER, PASS)


def save_config():

    # save running configuration, use local time to create new config file name

    command_output = execute('show run')
    timestr = time.strftime('%Y%m%d-%H%M%S')
    config_filename = '/bootflash/CONFIG_FILES/' + timestr + '_shrun'

    fileop1 = open(config_filename, 'w')
    fileop1.write(command_output)
    fileop1.close()

    fileop2 = open('/bootflash/CONFIG_FILES/current_config_name', 'w')
    fileop2.write(config_filename)
    fileop2.close()

    execute('copy run start')  # save the running config to startup
    return config_filename


def compare_configs(cfg1, cfg2):
    """
    This function, using the unified diff function, will compare two config files and identify the changes.
    '+' or '-' will be prepended in front of the lines with changes
    :param cfg1: old configuration file path and filename
    :param cfg2: new configuration file path and filename
    :return: text with the configuration lines that changed. The return will include the configuration for the sections
    that include the changes
    """

    # open the old and new configuration fiels
    f1 = open(cfg1, 'r')
    old_cfg = f1.readlines()
    f1.close()

    f2 = open(cfg2, 'r')
    new_cfg = f2.readlines()
    f2.close()

    # compare the two specified config files {cfg1} and {cfg2}
    d = difflib.unified_diff(old_cfg, new_cfg, n=9)

    # create a diff_list that will include all the lines that changed
    # create a diff_output string that will collect the generator output from the unified_diff function
    diff_list = []
    diff_output = ''

    for line in d:
        diff_output += line
        if line.find('Current configuration') == -1:
            if line.find('Last configuration change') == -1:
                if (line.find('+++') == -1) and (line.find('---') == -1):
                    if (line.find('-!') == -1) and (line.find('+!') == -1):
                        if line.startswith('+'):
                            diff_list.append('\n' + line)
                        elif line.startswith('-'):
                            diff_list.append('\n' + line)

    # process the diff_output to select only the sections between '!' characters for the sections that changed,
    # replace the empty '+' or '-' lines with space
    diff_output = diff_output.replace('+!', '!')
    diff_output = diff_output.replace('-!', '!')
    diff_output_list = diff_output.split('!')

    all_changes = []

    for changes in diff_list:
        for config_changes in diff_output_list:
            if changes in config_changes:
                if config_changes not in all_changes:
                    all_changes.append(config_changes)

    # create a config_text string with all the sections that include changes
    config_text = ''
    for items in all_changes:
        config_text += items

    return config_text


def create_room(room_name):

    # create webex teams room

    payload = {'title': room_name}
    url = WEBEX_TEAMS_URL + '/rooms'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    room_response = requests.post(url, data=json.dumps(payload), headers=header, verify=False)
    room_json = room_response.json()
    room_id = room_json['id']
    print('Created room with the name ' + room_name, 'room id: ' + str(room_id))
    return room_id


def add_room_membership(room_id, email_invite):

    # invite membership to the room id

    payload = {'roomId': room_id, 'personEmail': email_invite, 'isModerator': 'true'}
    url = WEBEX_TEAMS_URL + '/memberships'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    membership_response = requests.post(url, data=json.dumps(payload), headers=header, verify=False)
    membership_json = membership_response.json()
    try:
        membership = membership_json['personEmail']
    except:
        membership = None
    return membership


def delete_room(room_id):

    # delete room with the room id

    url = WEBEX_TEAMS_URL + '/rooms/' + room_id
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    response = requests.delete(url, headers=header, verify=False)


def post_room_message(room_id, message):

    # post message to the webex teams room with the room id

    payload = {'roomId': room_id, 'text': message}
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    response = requests.post(url, data=json.dumps(payload), headers=header, verify=False)


def last_user_message(room_id):
    # retrieve the last message from the room with the room id
    last_message_text = 'none'
    url = WEBEX_TEAMS_URL + '/messages?roomId=' + room_id
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    response = requests.get(url, headers=header, verify=False)
    list_messages_json = response.json()
    list_messages = list_messages_json['items']
    last_message_text = list_messages[0]['text']
    return str(last_message_text)


def get_restconf_hostname():

    # retrieve using RESTCONF the network device hostname

    url = 'https://' + HOST + '/restconf/data/Cisco-IOS-XE-native:native/hostname'
    header = {'Content-type': 'application/yang-data+json', 'accept': 'application/yang-data+json'}
    response = requests.get(url, headers=header, verify=False, auth=ROUTER_AUTH)
    hostname_json = response.json()
    hostname = hostname_json['Cisco-IOS-XE-native:hostname']
    return hostname


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
    url = SNOW_URL + '/table/incident'
    payload = {'short_description': description,
               'comments': (comment + ', \nIncident created using APIs by caller ' + username),
               'caller_id': caller_sys_id,
               'urgency': severity
               }
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    logging.debug('Create new incident')
    response = requests.post(url, auth=(SNOW_USER, SNOW_PASS), data=json.dumps(payload), headers=headers)
    incident_json = response.json()
    incident_number = incident_json['result']['number']
    logging.debug('Incident created: ' + incident_number)
    return incident_number


# main application

execute('send log Application config_change_approve.py started')

logging.basicConfig(
    filename='/bootflash/DEVWKS-1301-MEL19/application_run.log',
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

# select the user info that made changes from syslog message
syslog_input = execute('show logging | in %SYS-5-CONFIG_I')
syslog_lines = syslog_input.split('\n')
lines_no = len(syslog_lines)-2
user_info = syslog_lines[lines_no]

old_cfg_fn = '/bootflash/CONFIG_FILES/base-config'
new_cfg_fn = save_config()

diff = compare_configs(old_cfg_fn, new_cfg_fn)
print(diff)

f = open('/bootflash/CONFIG_FILES/diff', 'w')
f.write(diff)
f.close()


if diff != '':
    # find the device hostname using RESTCONF
    device_name = get_restconf_hostname()
    print('Hostname: ', str(device_name))
    webex_teams_room_id = create_room(WEBEX_TEAMS_SPACE)
    add_room_membership(webex_teams_room_id, WEBEX_TEAMS_MEMBER)
    post_room_message(webex_teams_room_id, 'The device with the hostname: ' + device_name + ', detected these configuration changes:')
    post_room_message(webex_teams_room_id, diff)
    post_room_message(webex_teams_room_id, '  \nConfiguration changed by user ' + user_info + '\n\n')
    post_room_message(webex_teams_room_id, 'Approve y/n ?')

    # start approval process
    approval_result = 'none'
    sleep(30)
    last_message = last_user_message(webex_teams_room_id)
    print('Last Webex Teams message: ', last_message)
    if last_message == 'n':
        # configuration changes not approved, rolled back
        execute('configure replace flash:/CONFIG_FILES/base-config force')
        approval_result = 'Configuration changes not approved, Configuration rollback to baseline'
        print(approval_result)
        logging.debug(approval_result)  # log to the application_log file
        post_room_message(webex_teams_room_id, approval_result)
    elif last_message == 'y':
        # configuration changes approved
        # save running configuration to the baseline file
        output = execute('show run')
        filename = '/bootflash/CONFIG_FILES/base-config'
        f = open(filename, 'w')
        f.write(output)
        f.close()
        approval_result = 'Configuration changes approved, Saved new baseline configuration'
        print(approval_result)
        logging.debug(approval_result)  # log to the application_log file
        post_room_message(webex_teams_room_id, approval_result)
    else:
        # approval request timeout, configuration roll back
        execute('configure replace flash:/CONFIG_FILES/base-config force')
        approval_result = 'Approval request timeout, Configuration rollback to baseline'
        print(approval_result)
        logging.debug(approval_result)  # log to the application_log file
        post_room_message(webex_teams_room_id, approval_result)

    post_room_message(webex_teams_room_id, 'This room will be deleted in 10 seconds')
    sleep(10)
    delete_room(webex_teams_room_id)

    comments = ('The device with the hostname: ' + device_name + ',\ndetected these configuration changes: \n' + diff)
    comments += ('\nConfiguration changed by user: ' + user_info + '\n' + approval_result)
    create_incident('Configuration Change Notification - ' + device_name, comments, SNOW_USER, 3)

execute('send log End Application Run')
logging.debug('End Application Run')

print('End Application Run')
