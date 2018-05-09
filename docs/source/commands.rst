Remote Scan Commands
~~~~~~~~~~~~~~~~~~~~~
This section documents required commands on the remote host for network scans.  In addition to the commands below, we depend on standard shell facilities like those provided by bash.

Basic Commands
##############
Below is a list of commands that do not require sudo or root access.

- cat
- ctime
- date
- echo
- egrep
- grep
- id
- sed
- sort
- rpm
- test
- tune2fs
- uname
- virsh
- whereis
- xargs


Sudo Commands
#############
Below is a list of commands that require sudo to gather facts.  Under each command there is a list of facts or categories of facts that will not be included in reports without sudo for that command.

- chkconfig:
    - EAP
    - Fuse on Karaf
- command
    - see dmicode
    - see subscription-manager
- dmidecode
    - cpu_socket_count
    - dmi_bios_vendor
    - dmi_bios_version
    - dmi_system_manufacturer
    - dmi_processor_family
    - dmi_system_uuid
    - virt_type
- find
    - BRMS
    - EAP
    - Fuse
    - Fuse on Karaf
- ifconfig
    - IP address
    - MAC address
- java
    - EAP info
- locate
    - BRMS
    - EAP
    - Fuse on Karaf
- ls
    - date_machine_id
    - EAP
    - Fuse on Karaf
    - BRMS
    - redhat_packages_certs
    - subman_consumed
- ps
    - EAP
    - Fuse on Karaf
    - virt type
- subscription-manager
    - subman_consumed
- systemctl
    - EAP
    - Fuse on Karaf
- unzip
    - EAP detection
- virt-what
    - virt_what_type
- yum
    - date_yum_history
    - yum_enabled_repolist
