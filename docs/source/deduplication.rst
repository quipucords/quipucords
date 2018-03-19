System Deduplication and Merging
================================
Quipucords is used to inspect and gather information about your IT infrastructure.  System information can be gathered using the following types of sources:

- network
- vcenter
- satellite

A scan is composed of one or more sources.  A single system may be seen through multiple sources during a scan.  For example, a vcenter VM may be running a Satellite managed RHEL OS installation.  A network source could also be used to scan this system.  In this case, the system will be reported via vcenter, satellite, and network sources during a scan.  Quipucords feeds unprocessed system facts from a scan into a fingerprint engine.  The fingerprint engine matches and merges data for systems seen in more than one source.

Deduplication of Systems
------------------------
Quipucords uses specific system facts to identify duplicate systems.  The following phases remove duplicate systems:

1. All systems from network sources are combined into a single network system set.  Systems are considered to be a duplicate if they have the same fact value for ``subscription_manager_id`` or ``bios_uuid``.
2. All systems from vcenter sources are combined into a single vcenter system set.  Systems are considered to be a duplicate if they have the same fact value for ``vm_uuid``.
3. All systems from satellite sources are combined into a single satellite system set.  Systems are considered to be a duplicate if they have the same fact value for ``subscription_manager_id``.
4. The network system set is merged with the satellite system set to form a single network-satellite system set.  Systems are considered to be a duplicate if they have the same fact value for ``subscription_manager_id`` or a matching MAC address in the ``mac_addresses`` fact.
5. The network-satellite system set is merged with the vcenter system set to form the complete system set.  Systems are considered to be a duplicate if they a matching MAC address in the ``mac_addresses`` fact or if the vcenter fact value of ``vm_uuid`` matches the network/satellite value of ``bios_uuid``.

Merging Systems
---------------
Once Quipucords determines that two systems are duplicates it performs a merge.  The merged system will have a union of system facts from each source.  When merging a fact that appears in both systems, the precedence from highest to lower is:

1. network
2. satellite
3. vcenter


Post Processing
---------------
After deduplication and merging have completed, there is a post processing phase used to create derived system facts.  Derived system facts are generated from more than one system fact.

System Creation Date
^^^^^^^^^^^^^^^^^^^^
``system_creation_date`` is a derived system fact.  The ``system_creation_date`` is determine by the following primitive facts.  The primitive facts below are ordered according to the accuracy of matching the real system creation time.  The highest non-empty value will be used.

1. date_machine_id
2. registration_time
3. date_anaconda_log
4. date_filesystem_create
5. date_yum_history
