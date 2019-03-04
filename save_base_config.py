
# developed by Gabi Zapodeanu, TSA, Global Partner Organization

import cli
from cli import cli, execute, configure

# add additional vty lines, two required for EEM
# save baseline running configuration


configure('no ip http active-session-modules none ; line vty 0 15 ; length 0 ; transport input ssh ; exit')


output = execute('show run')
filename = '/bootflash/CONFIG_FILES/base-config'

f = open(filename, 'w')
f.write(output)
f.close()

execute('copy run start')

print('\nEnd of saving configuration app\n')