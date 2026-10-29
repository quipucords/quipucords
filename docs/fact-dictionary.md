# Discovery Facts Data Dictionary

> **Auto-generated** from the quipucords source code by
> `scripts/generate_fact_dictionary.py`. Do not edit manually.

## Network (SSH/Ansible)

| Raw Fact | Role | Collection Method | Fingerprint Fact |
|----------|------|-------------------|-----------------|
| `user_has_sudo` | check_dependencies | `echo "user has sudo" 2>/dev/null` |  |
| `cloud_provider` | cloud_provider | `_(post-processed)_` | cloud_provider |
| `dmi_chassis_asset_tag` | cloud_provider | `dmidecode -t chassis 2>/dev/null \| grep "Asset Tag"` |  |
| `dmi_system_product_name` | cloud_provider | `dmidecode -t system 2>/dev/null \| grep "Product Name"` |  |
| `connection_host` | connection | `_(post-processed)_` |  |
| `connection_port` | connection | `_(post-processed)_` |  |
| `connection_timestamp` | connection | `_(post-processed)_` | system_last_checkin_date |
| `connection_uuid` | connection | `_(post-processed)_` |  |
| `cpu_core_count` | cpu | `_(post-processed)_` | cpu_core_count |
| `cpu_core_per_socket` | cpu | `cat /proc/cpuinfo 2>/dev/null \| grep '^cpu cores\s*.' \| sed -n -e 's/^.*cpu...` | cpu_core_per_socket |
| `cpu_count` | cpu | `cat /proc/cpuinfo 2>/dev/null \| grep '^processor\s*.' \| wc -l` | cpu_count |
| `cpu_hyperthreading` | cpu | `_(post-processed)_` | cpu_hyperthreading |
| `cpu_model_name` | cpu | `cat /proc/cpuinfo 2>/dev/null \| grep '^model name\s*.' \| sed -n -e 's/^.*mo...` |  |
| `cpu_model_ver` | cpu | `cat /proc/cpuinfo 2>/dev/null \| grep '^model\s*:' \| sed -n -e 's/^.*model\s...` |  |
| `cpu_siblings` | cpu | `cat /proc/cpuinfo 2>/dev/null \| grep '^siblings\s*.' \| sed -n -e 's/^.*sibl...` |  |
| `cpu_socket_count` | cpu | `cat /proc/cpuinfo 2>/dev/null \| grep 'physical id' \| sort -u \| wc -l` | cpu_socket_count |
| `cpu_vendor_id` | cpu | `cat /proc/cpuinfo 2>/dev/null \| grep '^vendor_id\s*' \| sed -n -e 's/^.*vend...` |  |
| `date_anaconda_log` | date | `ls --full-time /root/anaconda-ks.cfg 2>/dev/null \| grep -o '[0-9]\{4\}-[0-9]...` | date_anaconda_log |
| `date_filesystem_create` | date | `fs_date=$(tune2fs -l $(mount \| egrep '/ type' \| grep -o '/dev.* on' \| sed ...` | date_filesystem_create |
| `date_machine_id` | date | `if [ -f /etc/machine-id ] ; then ls --full-time /etc/machine-id 2>/dev/null \...` | date_machine_id |
| `dmi_bios_vendor` | dmi | `dmidecode -s bios-vendor 2>/dev/null` |  |
| `dmi_bios_version` | dmi | `dmidecode -s bios-version 2>/dev/null` |  |
| `dmi_system_manufacturer` | dmi | `dmidecode 2>/dev/null \| grep -A4 'System Information' \| grep 'Manufacturer'...` |  |
| `dmi_system_uuid` | dmi | `dmidecode -s system-uuid 2>/dev/null` | bios_uuid |
| `etc_machine_id` | etc_release | `if [ -f /etc/machine-id ]; then cat /etc/machine-id; fi \| tr -d '\r' \| tr -...` | etc_machine_id |
| `etc_release_name` | etc_release | `cat {{ internal_release_file }}` | os_name |
| `etc_release_release` | etc_release | `_(post-processed)_` | os_release |
| `etc_release_version` | etc_release | `_(post-processed)_` | os_version |
| `host_done` | host_done | `_(post-processed)_` |  |
| `hostnamectl` | hostnamectl | `export LANG=C LC_ALL=C TERM=dumb; hostnamectl status` |  |
| `ifconfig_ip_addresses` | ifconfig | `if command -v ifconfig >/dev/null ; then ifconfig -a; else hostname -I 2>/dev...` |  |
| `ifconfig_mac_addresses` | ifconfig | `ifconfig -a \|  grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'` |  |
| `insights_client_id` | insights | `if [ -f /etc/insights-client/machine-id ] ; then cat /etc/insights-client/mac...` | insights_client_id |
| `installed_products` | installed_products | `find /etc/pki/product*/ -name '*pem' -exec rct cat-cert --no-content '{}' \; ...` | installed_products |
| `ip_address_show_ipv4` | ip | `ip address show \| cat -` |  |
| `ip_address_show_ipv6` | ip | `_(post-processed)_` |  |
| `ip_address_show_mac` | ip | `_(post-processed)_` |  |
| `eap_home_bin` | jboss_eap | `ls -1 "{{ item }}"/bin 2>/dev/null` |  |
| `eap_home_candidates` | jboss_eap | `_(post-processed)_` |  |
| `eap_home_jboss_modules_manifest` | jboss_eap | `unzip -p "{{ item }}"/jboss-modules.jar META-INF/MANIFEST.MF 2>/dev/null` |  |
| `eap_home_jboss_modules_version` | jboss_eap | `java -jar "{{ item }}"/jboss-modules.jar -version 2>/dev/null` |  |
| `eap_home_layers` | jboss_eap | `ls -1 "{{ item }}"/modules/system/layers 2>/dev/null` |  |
| `eap_home_layers_conf` | jboss_eap | `cat '{{ item }}/modules/layers.conf' 2>/dev/null` |  |
| `eap_home_ls` | jboss_eap | `ls -1 "{{ item }}" 2>/dev/null` |  |
| `eap_home_readme_txt` | jboss_eap | `cat '{{ item }}/README.txt' 2>/dev/null` |  |
| `eap_home_version_txt` | jboss_eap | `cat '{{ item }}/version.txt' 2>/dev/null` |  |
| `jboss_eap_chkconfig` | jboss_eap | `chkconfig --list` |  |
| `jboss_eap_common_files` | jboss_eap | `test -e "{{ item }}"` |  |
| `jboss_eap_find_jboss_modules_jar` | jboss_eap | `find {{search_directories}} -xdev -type f -name jboss-modules.jar 2> /dev/nul...` |  |
| `jboss_eap_id_jboss` | jboss_eap | `id -u jboss` |  |
| `jboss_eap_jar_ver` | jboss_eap | `FOUND=""; for jar in `find {{search_directories}} -xdev -name 'jboss-modules....` |  |
| `jboss_eap_locate_jboss_modules_jar` | jboss_eap | `locate jboss-modules.jar \| xargs -n 1 --no-run-if-empty dirname` |  |
| `jboss_eap_packages` | jboss_eap | `rpm -qa --qf "%{NAME}\|%{VERSION}\|%{RELEASE}\|%{INSTALLTIME}\|%{VENDOR}\|%{B...` |  |
| `jboss_eap_run_jar_ver` | jboss_eap | `FOUND=""; for jar in `find {{search_directories}} -xdev -name 'run.jar' 2>/de...` |  |
| `jboss_eap_running_paths` | jboss_eap | `for proc_pid in $(find /proc -maxdepth 1 -xdev -name "[0-9]*" 2>/dev/null); d...` |  |
| `jboss_eap_systemctl_unit_files` | jboss_eap | `export LANG=C LC_ALL=C TERM=dumb; systemctl list-unit-files --no-pager` |  |
| `jboss_fuse_on_eap_activemq_ver` | jboss_eap | `ls -1 '{{ item }}/modules/system/layers/fuse/org/apache/activemq/main' 2>/dev...` |  |
| `jboss_fuse_on_eap_camel_ver` | jboss_eap | `ls -1 '{{ item }}/modules/system/layers/fuse/org/apache/camel/core/main' 2>/d...` |  |
| `jboss_fuse_on_eap_cxf_ver` | jboss_eap | `ls -1 '{{ item }}/modules/system/layers/base/org/apache/cxf/impl/main' 2>/dev...` |  |
| `jboss_processes` | jboss_eap | `ps -A -o comm -o args e --columns 10000 \| grep java \| grep jboss \| grep -v...` |  |
| `eap5_home_candidates` | jboss_eap5 | `ps -A -o comm -o args e --columns 10000 \| egrep '^java.*(eap\|jboss).*' \| t...` |  |
| `eap5_home_ls_jboss_as` | jboss_eap5 | `ls -1 '{{ item }}/jboss-as' 2>/dev/null` |  |
| `eap5_home_readme_html` | jboss_eap5 | `cat '{{ item }}/readme.html' 2>/dev/null` |  |
| `eap5_home_run_jar_manifest` | jboss_eap5 | `unzip -p '{{ item }}/jboss-as/bin/run.jar' META-INF/MANIFEST.MF` |  |
| `eap5_home_run_jar_version` | jboss_eap5 | `java -jar '{{ item }}/jboss-as/bin/run.jar' --version` |  |
| `eap5_home_version_txt` | jboss_eap5 | `cat '{{ item }}/version.txt' 2>/dev/null` |  |
| `jboss_activemq_ver` | jboss_fuse | `FOUND=""; for jar in `find {{search_directories}} -type f -xdev -name \*activ...` |  |
| `jboss_camel_ver` | jboss_fuse | `FOUND=""; for jar in `find {{search_directories}} -type f -xdev -name \*camel...` |  |
| `jboss_cxf_ver` | jboss_fuse | `FOUND=""; for jar in `find {{search_directories}} -type f -xdev -name \*cxf-r...` |  |
| `fuse_activemq_version` | jboss_fuse_on_karaf | `_(post-processed)_` |  |
| `fuse_camel_version` | jboss_fuse_on_karaf | `_(post-processed)_` |  |
| `fuse_cxf_version` | jboss_fuse_on_karaf | `_(post-processed)_` |  |
| `jboss_fuse_activemq_ver` | jboss_fuse_on_karaf | `locate activemq \| grep fuse \| sed -n 's/^.*\(redhat-[0-9]\{6\}\).*/\1/p'` |  |
| `jboss_fuse_camel_ver` | jboss_fuse_on_karaf | `locate camel-core \| grep fuse \| sed -n 's/.*\(redhat-[0-9]\{6\}\).*/\1/p'` |  |
| `jboss_fuse_chkconfig` | jboss_fuse_on_karaf | `chkconfig --list` |  |
| `jboss_fuse_cxf_ver` | jboss_fuse_on_karaf | `locate cxf-rt \| grep fuse \| sed -n 's/^.*\(redhat-[0-9]\{6\}\).*/\1/p'` |  |
| `jboss_fuse_on_karaf_activemq_ver` | jboss_fuse_on_karaf | `ls -1 '{{ item }}/system/org/apache/activemq/activemq-camel' 2>/dev/null \| g...` |  |
| `jboss_fuse_on_karaf_camel_ver` | jboss_fuse_on_karaf | `ls -1 '{{ item }}/system/org/apache/camel/camel-core' 2>/dev/null \| grep fus...` |  |
| `jboss_fuse_on_karaf_cxf_ver` | jboss_fuse_on_karaf | `ls -1 '{{ item }}/system/org/apache/cxf/cxf-rt-bindings-coloc' 2>/dev/null \|...` |  |
| `jboss_fuse_systemctl_unit_files` | jboss_fuse_on_karaf | `export LANG=C LC_ALL=C TERM=dumb; systemctl list-unit-files --no-pager` |  |
| `karaf_find_karaf_jar` | jboss_fuse_on_karaf | `find {{search_directories}} -xdev -type f -name karaf.jar 2> /dev/null \| sed...` |  |
| `karaf_home_bin_fuse` | jboss_fuse_on_karaf | `ls -1 "{{ item }}"/bin/fuse 2>/dev/null` |  |
| `karaf_home_system_org_jboss` | jboss_fuse_on_karaf | `ls -1 "{{ item }}"/system/org/jboss 2>/dev/null` |  |
| `karaf_homes` | jboss_fuse_on_karaf | `_(post-processed)_` |  |
| `karaf_locate_karaf_jar` | jboss_fuse_on_karaf | `locate karaf.jar \| sed -n -e 's/\(.*\)lib\/karaf\.jar$/\1/p' \| xargs -n 1 -...` |  |
| `karaf_running_processes` | jboss_fuse_on_karaf | `ps -A -o args \| egrep --invert-match '(^sed)\|(\\| sed)' \| sed -n -e 's/.*-...` |  |
| `jws_has_cert` | jboss_ws | `ls /etc/pki/product/185.pem /etc/pki/product-default/185.pem 2>/dev/null \| s...` |  |
| `jws_has_eula_txt_file` | jboss_ws | `if [ -f "{{ jws_home }}"/JBossEULA.txt ]; then FOUND="true"; else FOUND="fals...` |  |
| `jws_home` | jboss_ws | `ls -d1 "{{ item }}" 2>/dev/null` |  |
| `jws_home_candidates` | jboss_ws | `find {{search_directories}} -type d 2>/dev/null \| egrep '(ews\|jws).*[0-9]+\...` |  |
| `jws_installed_with_rpm` | jboss_ws | `yum -C grouplist {{item}} 2>/dev/null \| grep -A1 'Installed Groups:' \| grep...` |  |
| `jws_version` | jboss_ws | `export LANG=C LC_ALL=C TERM=dumb; systemctl status 'jws*-tomcat.service' 2>/d...` |  |
| `system_memory_bytes` | memory | `set -o pipefail cat /proc/meminfo \| grep MemTotal \| awk '{print $2}'` | system_memory_bytes |
| `redhat_packages_certs` | redhat_packages | `ls /etc/pki/product/ /etc/pki/product-default/ 2> /dev/null \|grep '.pem' \| ...` | redhat_certs |
| `redhat_packages_gpg_is_redhat` | redhat_packages | `SIG="%{DSAHEADER:pgpsig}\|%{RSAHEADER:pgpsig}\|%{SIGGPG:pgpsig}\|%{SIGPGP:pgp...` | is_redhat |
| `redhat_packages_gpg_last_built` | redhat_packages | `SIG="%{DSAHEADER:pgpsig}\|%{RSAHEADER:pgpsig}\|%{SIGGPG:pgpsig}\|%{SIGPGP:pgp...` |  |
| `redhat_packages_gpg_last_installed` | redhat_packages | `SIG="%{DSAHEADER:pgpsig}\|%{RSAHEADER:pgpsig}\|%{SIGGPG:pgpsig}\|%{SIGPGP:pgp...` |  |
| `redhat_packages_gpg_num_installed_packages` | redhat_packages | `rpm -qa \| wc -l` |  |
| `redhat_packages_gpg_num_rh_packages` | redhat_packages | `SIG="%{DSAHEADER:pgpsig}\|%{RSAHEADER:pgpsig}\|%{SIGGPG:pgpsig}\|%{SIGPGP:pgp...` | redhat_package_count |
| `yum_enabled_repolist` | redhat_packages | `yum -C repolist enabled 2> /dev/null` |  |
| `redhat_release_name` | redhat_release | `rpm -q --queryformat "%{NAME}\n%{VERSION}\n%{RELEASE}\n" --whatprovides redha...` |  |
| `redhat_release_release` | redhat_release | `_(post-processed)_` |  |
| `redhat_release_version` | redhat_release | `_(post-processed)_` |  |
| `azure_offer` | subman | `subscription-manager facts --list 2>/dev/null \| grep '^azure_offer:' \| sed ...` |  |
| `subman` | subman | `ls /etc/rhsm/facts 2>/dev/null \| grep .facts \| wc -l` |  |
| `subman_consumed` | subman | `subscription-manager list --consumed 2>/dev/null \| grep -e '^SKU' -e '^Subsc...` |  |
| `subman_cpu_core_per_socket` | subman | `subscription-manager facts --list \| grep '^cpu.core(s)_per_socket.' \| sed -...` |  |
| `subman_cpu_cpu` | subman | `subscription-manager facts --list \| grep '^cpu.cpu(s).' \| sed -n -e 's/^.*c...` |  |
| `subman_cpu_cpu_socket` | subman | `subscription-manager facts --list \| grep '^cpu.cpu_socket(s).' \| sed -n -e ...` |  |
| `subman_overall_status` | subman | `subscription-manager status \| grep -e 'Overall Status:'\| cut -d ":" -f2` |  |
| `subman_virt_host_type` | subman | `subscription-manager facts --list \| grep '^virt.host_type.' \| sed -n -e 's/...` |  |
| `subman_virt_is_guest` | subman | `subscription-manager facts --list \| grep '^virt.is_guest.' \| sed -n -e 's/^...` |  |
| `subman_virt_uuid` | subman | `subscription-manager facts --list 2>/dev/null \| grep '^virt.uuid.' \| sed -n...` |  |
| `subscription_manager_id` | subman | `subscription-manager identity 2>/dev/null \| grep 'system identity:' \| sed '...` | subscription_manager_id |
| `system_purpose_json` | system_purpose | `if [ -f /etc/rhsm/syspurpose/syspurpose.json ] ; then cat /etc/rhsm/syspurpos...` | system_purpose |
| `uname_all` | uname | `uname -a` |  |
| `uname_hostname` | uname | `uname -n` | name |
| `uname_processor` | uname | `uname -p` | architecture |
| `system_user_count` | user_data | `cat /etc/passwd` | system_user_count |
| `virt_num_guests` | virt | `virsh -c qemu:///system --readonly list --all \| wc -l` |  |
| `virt_num_running_guests` | virt | `virsh -c qemu:///system --readonly list --uuid \| wc -l` |  |
| `virt_type` | virt | `model_name=$(cat /proc/cpuinfo 2>/dev/null \| grep '^model name\s*:' \| sed -...` | virtualized_type |
| `virt_virt` | virt | `_(post-processed)_` |  |
| `virt_what` | virt_what | `virt-what` |  |

<details><summary>30 internal/dependency facts</summary>

| Fact | Role | Command |
|------|------|---------|
| `internal_have_chkconfig` | check_dependencies | `command -v chkconfig` |
| `internal_have_dmidecode` | check_dependencies | `command -v dmidecode` |
| `internal_have_ifconfig` | check_dependencies | `command -v ifconfig` |
| `internal_have_ifconfig_user` | check_dependencies | `command -v ifconfig` |
| `internal_have_ip` | check_dependencies | `command -v ip` |
| `internal_have_ip_user` | check_dependencies | `command -v ip` |
| `internal_have_java` | check_dependencies | `command -v java` |
| `internal_have_locate` | check_dependencies | `locate echo` |
| `internal_have_rct_user` | check_dependencies | `command -v rct` |
| `internal_have_rpm_user` | check_dependencies | `command -v rpm` |
| `internal_have_subscription_manager` | check_dependencies | `command -v subscription-manager` |
| `internal_have_systemctl` | check_dependencies | `command -v systemctl` |
| `internal_have_tune2fs_user` | check_dependencies | `command -v tune2fs` |
| `internal_have_unzip` | check_dependencies | `command -v unzip` |
| `internal_have_virsh_user` | check_dependencies | `command -v virsh` |
| `internal_have_virt_what` | check_dependencies | `command -v virt-what` |
| `internal_have_yum` | check_dependencies | `command -v yum` |
| `internal_dmi_chassis_asset_tag` | cloud_provider | `dmidecode -t chassis 2>/dev/null \| grep "Asset Tag"` |
| `internal_dmi_system_product_name` | cloud_provider | `dmidecode -t system 2>/dev/null \| grep "Product Name"` |
| `internal_cpu_socket_count_cpuinfo` | cpu | `cat /proc/cpuinfo 2>/dev/null \| grep 'physical id' \| sort -u \| wc -l` |
| `internal_cpu_socket_count_dmi` | cpu | `dmidecode -t 4 \| egrep 'Designation\|Status'` |
| `internal_dmi_system_uuid` | dmi | `dmidecode -s system-uuid 2>/dev/null` |
| `internal_distro_standard_release` | etc_release | `_(computed)_` |
| `internal_release_file` | etc_release | `for i in \   /etc/debian_version \   {{ internal_distro_standard_release\|joi...` |
| `internal_system_user_count` | user_data | `cat /etc/passwd` |
| `internal_cpu_model_name_kvm` | virt | `model_name=$(cat /proc/cpuinfo 2>/dev/null \| grep '^model name\s*:' \| sed -...` |
| `internal_kvm_found` | virt | `if [ -e /dev/kvm ]; then echo "Y"; else echo "N"; fi` |
| `internal_sys_manufacturer` | virt | `dmidecode \| grep -A4 'System Information' \| grep 'Manufacturer' \| sed -n -...` |
| `internal_xen_guest` | virt | `ps aux \| grep xend \| grep -v grep \| wc -l` |
| `internal_xen_privcmd_found` | virt | `if [ -e /proc/xen/privcmd ]; then echo "Y"; else echo "N"; fi` |

</details>

## Satellite

| Raw Fact | Role | Collection Method | Fingerprint Fact |
|----------|------|-------------------|-----------------|
| `architecture` | satellite | `Satellite API: FACTS_MAPPING -> uname.machine` | architecture |
| `cores` | satellite | `Satellite API: FACTS_MAPPING -> cpu.cpu(s)` | cpu_core_count |
| `errata_out_of_date` | satellite | `Satellite API: ERRATA_MAPPING -> total` |  |
| `hostname` | satellite | `Satellite API: FIELDS_MAPPING -> name` | name |
| `ip_addresses` | satellite | `Satellite API` | ip_addresses |
| `is_virtualized` | satellite | `Satellite API: FACTS_MAPPING -> virt.is_guest` |  |
| `katello_agent_installed` | satellite | `Satellite API: CONTENT_FACET_MAPPING -> katello_agent_installed` |  |
| `kernel_version` | satellite | `Satellite API: FACTS_MAPPING -> uname.release` |  |
| `last_checkin_time` | satellite | `Satellite API: SUBS_FACET_MAPPING -> last_checkin` | system_last_checkin_date |
| `location` | satellite | `Satellite API` |  |
| `mac_addresses` | satellite | `Satellite API` | mac_addresses |
| `num_sockets` | satellite | `Satellite API: FACTS_MAPPING -> cpu.cpu_socket(s)` | cpu_socket_count |
| `organization` | satellite | `Satellite API: FIELDS_MAPPING -> organization_name` |  |
| `os_name` | satellite | `Satellite API` | is_redhat |
| `os_release` | satellite | `Satellite API: FIELDS_MAPPING -> operatingsystem_name` | os_release |
| `os_version` | satellite | `Satellite API` | os_version |
| `packages_out_of_date` | satellite | `Satellite API: ERRATA_MAPPING -> total` |  |
| `registered_by` | satellite | `Satellite API: SUBS_FACET_MAPPING -> registered_by` |  |
| `registration_time` | satellite | `Satellite API: SUBS_FACET_MAPPING -> registered_at` | registration_time |
| `uuid` | satellite | `Satellite API: SUBS_FACET_MAPPING -> uuid` | subscription_manager_id |
| `virt_type` | satellite | `Satellite API: FACTS_MAPPING -> virt.host_type` | virtualized_type |
| `virtual_host_name` | satellite | `Satellite API: VIRTUAL_HOST_MAPPING -> name` | virtual_host_name |
| `virtual_host_uuid` | satellite | `Satellite API: VIRTUAL_HOST_MAPPING -> uuid` | virtual_host_uuid |

## vCenter

| Raw Fact | Role | Collection Method | Fingerprint Fact |
|----------|------|-------------------|-----------------|
| `cluster.datacenter` | vcenter/cluster | `pyVmomi (cluster)` |  |
| `cluster.name` | vcenter/cluster | `pyVmomi (cluster)` |  |
| `host.cluster` | vcenter/host | `pyVmomi (host)` |  |
| `host.cpu_cores` | vcenter/host | `pyVmomi (host)` |  |
| `host.cpu_count` | vcenter/host | `pyVmomi (host)` |  |
| `host.cpu_threads` | vcenter/host | `pyVmomi (host)` |  |
| `host.datacenter` | vcenter/host | `pyVmomi (host)` |  |
| `host.name` | vcenter/host | `pyVmomi (host)` |  |
| `host.uuid` | vcenter/host | `pyVmomi (host)` |  |
| `vm.cluster` | vcenter/vm | `pyVmomi (vm)` | vm_cluster |
| `vm.cpu_count` | vcenter/vm | `pyVmomi (vm)` | cpu_count |
| `vm.datacenter` | vcenter/vm | `pyVmomi (vm)` | vm_datacenter |
| `vm.dns_name` | vcenter/vm | `pyVmomi (vm)` | vm_dns_name |
| `vm.host.cpu_cores` | vcenter/vm | `pyVmomi (vm)` | vm_host_core_count |
| `vm.host.cpu_count` | vcenter/vm | `pyVmomi (vm)` | vm_host_socket_count |
| `vm.host.cpu_threads` | vcenter/vm | `pyVmomi (vm)` |  |
| `vm.host.name` | vcenter/vm | `pyVmomi (vm)` | virtual_host_name |
| `vm.host.uuid` | vcenter/vm | `pyVmomi (vm)` | virtual_host_uuid |
| `vm.ip_addresses` | vcenter/vm | `pyVmomi (vm)` | ip_addresses |
| `vm.is_template` | vcenter/vm | `pyVmomi (vm)` |  |
| `vm.last_check_in` | vcenter/vm | `pyVmomi (vm)` | system_last_checkin_date |
| `vm.mac_addresses` | vcenter/vm | `pyVmomi (vm)` | mac_addresses |
| `vm.memory_size` | vcenter/vm | `pyVmomi (vm)` |  |
| `vm.name` | vcenter/vm | `pyVmomi (vm)` |  |
| `vm.os` | vcenter/vm | `pyVmomi (vm)` | is_redhat |
| `vm.state` | vcenter/vm | `pyVmomi (vm)` | vm_state |
| `vm.uuid` | vcenter/vm | `pyVmomi (vm)` | vm_uuid |

## OpenShift (OCP)

| Raw Fact | Role | Collection Method | Fingerprint Fact |
|----------|------|-------------------|-----------------|
| `cluster.uuid` | openshift/cluster | `OCP API: cluster` |  |
| `cluster.version` | openshift/cluster | `OCP API: cluster` |  |
| `operators` | openshift/cluster | `OCP API: aggregate` |  |
| `rhacm_metrics` | openshift/cluster | `OCP API: aggregate` |  |
| `workloads` | openshift/cluster | `OCP API: aggregate` |  |
| `node.addresses` | openshift/node | `OCP API: nodes` | ip_addresses |
| `node.allocatable` | openshift/node | `OCP API: nodes` |  |
| `node.architecture` | openshift/node | `OCP API: nodes` | architecture |
| `node.capacity` | openshift/node | `OCP API: nodes` |  |
| `node.cluster_uuid` | openshift/node | `OCP API: nodes` | vm_cluster |
| `node.creation_timestamp` | openshift/node | `OCP API: nodes` | system_creation_date |
| `node.kernel_version` | openshift/node | `OCP API: nodes` |  |
| `node.labels` | openshift/node | `OCP API: nodes` | system_role |
| `node.machine_id` | openshift/node | `OCP API: nodes` | etc_machine_id |
| `node.name` | openshift/node | `OCP API: nodes` | name |
| `node.operating_system` | openshift/node | `OCP API: nodes` |  |
| `node.taints` | openshift/node | `OCP API: nodes` |  |
| `node.unschedulable` | openshift/node | `OCP API: nodes` |  |
| `workload.container_images` | openshift/workload | `OCP API: workloads` |  |
| `workload.init_container_images` | openshift/workload | `OCP API: workloads` |  |
| `workload.labels` | openshift/workload | `OCP API: workloads` |  |
| `workload.name` | openshift/workload | `OCP API: workloads` |  |
| `workload.namespace` | openshift/workload | `OCP API: workloads` |  |

## Ansible Automation Platform (AAP)

| Raw Fact | Role | Collection Method | Fingerprint Fact |
|----------|------|-------------------|-----------------|
| `comparison` | ansible | `(computed)` |  |
| `hosts` | ansible | `AAP API: /api/v2/hosts/` |  |
| `instance_details` | ansible | `AAP API: /api/v2/ (ping + me)` | instance_details__system_name -> name, instance_details__version -> os_version |
| `jobs` | ansible | `AAP API: /api/v2/jobs/ or host_metrics` |  |

## Red Hat Advanced Cluster Security (RHACS)

| Raw Fact | Role | Collection Method | Fingerprint Fact |
|----------|------|-------------------|-----------------|
| `secured_units_current` | rhacs | `RHACS API: /v1/.../secured-units/current` |  |
| `secured_units_max` | rhacs | `RHACS API: /v1/.../secured-units/max` |  |
