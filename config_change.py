
# developed by Gabi Zapodeanu, TSA, Global Partner Organization


from cli import cli
import time
import difflib
import requests
import json

from config import WEBEX_TEAMS_URL, WEBEX_TEAMS_AUTH, WEBEX_TEAMS_SPACE, WEBEX_TEAMS_MEMBER
from config import HOST, USER, PASS
from config import SNOW_URL, SNOW_USER, SNOW_PASS

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.auth import HTTPBasicAuth  # for Basic Auth

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # Disable insecure https warnings


ROUTER_AUTH = HTTPBasicAuth(USER, PASS)


def save_config():

    # save running configuration, use local time to create new config file name

    output = cli('show run')
    timestr = time.strftime('%Y%m%d-%H%M%S')
    filename = '/bootflash/CONFIG_FILES/' + timestr + '_shrun'

    f = open(filename, 'w')
    f.write(output)
    f.close

    f = open('/bootflash/CONFIG_FILES/current_config_name', 'w')
    f.write(filename)
    f.close

    return filename


def compare_configs(cfg1, cfg2):

    # compare two config files

    d = difflib.unified_diff(cfg1, cfg2)

    diffstr = ''

    for line in d:
        if line.find('Current configuration') == -1:
            if line.find('Last configuration change') == -1:
                if (line.find('+++') == -1) and (line.find('---') == -1):
                    if (line.find('-!') == -1) and (line.find('+!') == -1):
                       if line.startswith('+'):
                            diffstr = diffstr + '\n' + line
                       elif line.startswith('-'):
                            diffstr = diffstr + '\n' + line

    return diffstr


def create_room(room_name):

    # create spark room

    payload = {'title': room_name}
    url = WEBEX_TEAMS_URL + '/rooms'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    room_response = requests.post(url, data=json.dumps(payload), headers=header, verify=False)
    room_json = room_response.json()
    room_id = room_json['id']
    print('Created room with the name ' + room_name, 'room id: ', room_id)
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
    print('Print delete room request status: ', response.status_code, room_id)


def post_room_message(room_id, message):

    # post message to the Spark room with the room id

    payload = {'roomId': room_id, 'text': message}
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    requests.post(url, data=json.dumps(payload), headers=header, verify=False)


def last_user_message(room_id):

    # retrieve the last message from the room with the room id

    url = WEBEX_TEAMS_URL + '/messages?roomId=' + room_id
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    response = requests.get(url, headers=header, verify=False)
    list_messages_json = response.json()
    list_messages = list_messages_json['items']
    last_message = list_messages[0]['text']
    return last_message


def get_restconf_hostname():

    # retrieve using RETSCONF the network device hostname

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
    print caller_sys_id
    url = SNOW_URL + '/table/incident'
    payload = {'short_description': description,
               'comments': (comment + ', \nIncident created using APIs by caller ' + username),
               'caller_id': caller_sys_id,
               'urgency': severity
               }
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(url, auth=(SNOW_USER, SNOW_PASS), data=json.dumps(payload), headers=headers)
    incident_json = response.json()
    return incident_json['result']['number']


# main application

syslog_input = cli('show logging | in %SYS-5-CONFIG_I')
syslog_lines = syslog_input.split('\n')
lines_no = len(syslog_lines)-2
user_info = syslog_lines[lines_no]

old_cfg_fn = '/bootflash/CONFIG_FILES/base-config'
new_cfg_fn = save_config()

f = open(old_cfg_fn)
old_cfg = f.readlines()
f.close

f = open(new_cfg_fn)
new_cfg = f.readlines()
f.close

diff = compare_configs(old_cfg,new_cfg)
print diff

f = open('/bootflash/CONFIG_FILES/diff', 'w')
f.write(diff)
f.close

if diff != '':
    # find the device hostname using RESTCONF
    device_name = get_restconf_hostname()
    print('Hostname: ', device_name)
    spark_room_id = create_room(WEBEX_TEAMS_SPACE)
    add_room_membership(spark_room_id, WEBEX_TEAMS_MEMBER)
    post_room_message(spark_room_id, 'The device with the hostname: ' + device_name + ', detected these configuration changes:')
    post_room_message(spark_room_id, diff)
    post_room_message(spark_room_id, '   ')
    post_room_message(spark_room_id, 'Configuration changed by user ' + user_info)
    post_room_message(spark_room_id, 'Approve y/n ?')
    counter = 6  # wait for approval = 10 seconds * counter, in this case 10 sec x 6 = 60 seconds
    last_message = last_user_message(spark_room_id)
    # start approval process
    while last_message == 'Approve y/n ?':
        time.sleep(10)
        last_message = last_user_message(spark_room_id)
        print(last_message)
        if last_message == 'n':
            cli('configure replace flash:/CONFIG_FILES/base-config force')
            approval_result = 'Configuration changes not approved, Configuration rollback to baseline'
            print('Configuration roll back completed')
            break
        else:
            if last_message == 'y':
                print('Configuration change approved')
                # save new baseline running configuration
                output = cli('show run')
                filename = '/bootflash/CONFIG_FILES/base-config'
                f = open(filename, "w")
                f.write(output)
                f.close
                print('Saved new baseline configuration')
                approval_result = 'Configuration changes approved, Saved new baseline configuration'
                break
            else:
                counter -= 1
                post_room_message(spark_room_id, 'Approve y/n ?')
                if counter == 0:
                    cli('configure replace flash:/CONFIG_FILES/base-config force')
                    approval_result = 'Approval request timeout, Configuration rollback to baseline'
                    print('Configuration roll back completed')
                    break

    post_room_message(spark_room_id, approval_result)

    post_room_message(spark_room_id, 'This room will be deleted in 30 seconds')
    time.sleep(10)
    delete_room(spark_room_id)

    comments = ('The device with the hostname: ' + device_name + ',\ndetected these configuration changes: \n' + diff + '\nConfiguration changed by user: ' + user_info + '\n' + approval_result)
    create_incident('Configuration Change Notification - ' + device_name, comments, SNOW_USER, 3)

print('End Application Run')
