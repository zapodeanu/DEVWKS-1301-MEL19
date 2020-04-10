# DEVWKS - 1301

**DEVWKS - 1301**
**NetDevOps Engineer Everyday Skills**

This repo will include all the files needed for the Cisco Live Melbourne 2019 DevNet DEVWKS - 1301 session.

Do you want to learn how to write simple ChatOps apps for IOS XE network devices?
This session will explore a few IOS XE device programmability capabilities to help
you create your first ChatOps application using NETCONF, RESTCONF, and Guest Shell.


**This workshop requires:**

- Cisco DevNet account
- Webex Teams account
- GitHub account
- ServiceNow developer account (optional)
- DevNet CSR1000V sandbox – provided, or reserved by you here: https://developer.cisco.com/site/sandbox/
- You will need Python 2.7 and 3.x installed
- requests and ncclient libraries

**The repo includes these files**

- config.py - configuration file that includes accounts username and password
- eem_cli_config.txt - cli configuration for the CSR1000V router that will be used during the workshop
- save_base_config.py - script to establish the baseline configuration
- netconf_restconf.py - demonstrate how to manage the IOS XE device from Guest Shell using NETCONF and RESTCONF
- create_incident.py - create a new ServiceNow incident
- config_change_incident.py - test Embedded Event Manager and Guest Shell 
- config_change_approve.py - application code

**Application Workflow**

- User makes IOS XE device configuration change
- Syslog triggers EEM Guest Shell Python script execution
- The config_change.py script will:
    - Detect if a configuration change
    - Collect the device hostname using RESTCONF
    - Identify the user that made the change using Python CLI
    - Identify the configuration changes
    - Create Webex Teams room using REST APIs, invite Approver to room, post the above information to ask for approval
    - If changes approved, save new configuration as baseline
    - If not approved or no response, rollback to the previous baseline configuration
    - Close the Webex Teams room in 30 seconds (it is used for the Approval Process)
    - Create ServiceNow incident to record all the above information


