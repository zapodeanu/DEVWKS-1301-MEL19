
# developed by Gabi Zapodeanu, TSA, Global Partner Organization

from cli import cli

# add additional vty lines, two required for EEM
# save baseline running configuration

cli('configure terminal ; line vty 0 15 ; length 0 ; transport input ssh ; exit')

output = cli('show run')
filename = '/bootflash/CONFIG_FILES/base-config'

f = open(filename, "w")
f.write(output)
f.close