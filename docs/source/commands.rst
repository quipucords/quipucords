Commands Used in Scans of Remote Network Assets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When you run a network scan, Quipucords must use the credentials that you provide to run certain commands on the remote systems in your network. Some of those commands must run with elevated privileges. This access is typically acquired through the use of the sudo command or similar commands. The elevated privileges are required to gather the types of facts that Quipucords uses to build the report about your installed products and consumed entitlements.

Although it is possible to run a scan for a network source without elevated privileges, the results of that scan will be incomplete. The incomplete results from the network scan will affect the quality of the generated report for the scan.

The following information lists the commands that Quipucords runs on remote hosts during a network scan. The information includes the basic commands that can run without elevated privileges and the commands that must run with elevated privileges to gather the most accurate and complete information for the report.

**NOTE:** In addition to the following commands, Quipucords also depends on standard shell facilities, such as those provided by the Bash shell.

Basic Commands
++++++++++++++
The following commands do not require elevated privileges to gather facts:

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


Commands that Need Elevated Privileges
++++++++++++++++++++++++++++++++++++++
The following commands require elevated privileges to gather facts. Each command includes a list of individual facts or categories of facts that cannot be included in reports if elevated privileges are not available for that command.

- chkconfig
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
