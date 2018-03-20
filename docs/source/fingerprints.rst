System Fingerprints
===================
A system fingerprint is composed of a set of system facts, products, entitlements, sources, and metadata. The following example shows a system fingerprint. ::

    {
        "os_release": "Red Hat Enterprise Linux Atomic Host 7.4",
        "cpu_count": 4,
        "products": [
            {
                "name": "JBoss EAP",
                "version": null,
                "presence": "absent",
                "metadata": {
                    "source_id": 5,
                    "source_name": "S62Source",
                    "source_type": "satellite",
                    "raw_fact_key": null
                }
            }
        ],
        "entitlements": [
            {
                "name": "Satellite Tools 6.3",
                "entitlement_id": 54,
                "metadata": {
                    "source_id": 5,
                    "source_name": "S62Source",
                    "source_type": "satellite",
                    "raw_fact_key": "entitlements"
                }
            }
        ],
        "metadata": {
            "os_release": {
                "source_id": 5,
                "source_name": "S62Source",
                "source_type": "satellite",
                "raw_fact_key": "os_release"
            },
            "cpu_count": {
                "source_id": 4,
                "source_name": "NetworkSource",
                "source_type": "network",
                "raw_fact_key": "os_release"
            }
        },
        "sources": [
            {
                "id": 4,
                "source_type": "network",
                "name": "NetworkSource"
            },
            {
                "id": 5,
                "source_type": "satellite",
                "name": "S62Source"
            }
        ]
    }

A scan produces system facts.  As an example, the ``os_release`` describes the operation system and release used by the system.  For each system fact, there is a corresponding entry in the metadata object that identifies the original source of the system fact.

Each fingerprint contains an entitlement list.  The entitlement has a name, id, and metadata describing the original source.  In the example previous example, the system has the ``Satellite Tools 6.3`` entitlement.

A system fingerprint also contains a list of products.  A product has a name, version, presence, and metadata field.  The system above has JBoss EAP installed.

Lastly, each system fingerprint has a list of sources which contained this system.  A system can be contained in more than one source.


System Deduplication and Merging
===================
Quipucords is used to inspect and gather information about your IT infrastructure.  System information can be gathered using the following types of sources:

- network
- vcenter
- satellite

A scan is composed of one or more sources. A single system can be found in multiple sources during a scan. For example, a virtual machine on vCenter server could be running a Satellite managed RHEL OS installation. A network source could also be used to scan this system. In this case, the system will be reported via vcenter, satellite, and network sources during a scan. Quipucords feeds unprocessed system facts from a scan into a fingerprint engine. The fingerprint engine matches and merges data for systems seen in more than one source.

Deduplication of Systems
------------------------
Quipucords uses specific system facts to identify duplicate systems. The following phases remove duplicate systems during the deduplication process:

1. All systems from network sources are combined into a single network system set. Systems are considered to be duplicates if they have the same fact value for ``subscription_manager_id`` or ``bios_uuid``.
2. All systems from vcenter sources are combined into a single vcenter system set. Systems are considered to be duplicates if they have the same fact value for ``vm_uuid``.
3. All systems from satellite sources are combined into a single satellite system set. Systems are considered to be duplicates if they have the same fact value for ``subscription_manager_id``.
4. The network system set is merged with the satellite system set to form a single network-satellite system set. Systems are considered to be duplicates if they have the same fact value for ``subscription_manager_id`` or a matching MAC address in the ``mac_addresses`` fact.
5. The network-satellite system set is merged with the vcenter system set to form the complete system set. Systems are considered to be duplicates if they have a matching MAC address in the ``mac_addresses`` fact or if the vcenter fact value of ``vm_uuid`` matches the network value of ``bios_uuid``.

Merging Systems
---------------
After Quipucords determines that two systems are duplicates it performs a merge. The merged system will have a union of system facts from each source. When merging a fact that appears in both systems, the precedence from highest to lowest is:

1. network
2. satellite
3. vcenter

A system fingerprint contains a ``metadata`` dictionary that captures the original source of each system fact.


Post Processing
---------------
After deduplication and merging are complete, there is a post processing phase used to create derived system facts. Derived system facts are generated from more than one system fact.

System Creation Date
^^^^^^^^^^^^^^^^^^^^
``system_creation_date`` is a derived system fact. The ``system_creation_date`` is determined by the following primitive facts. The primitive facts below are ordered according to the accuracy of matching the real system creation time. The highest non-empty value will be used.

1. date_machine_id
2. registration_time
3. date_anaconda_log
4. date_filesystem_create
5. date_yum_history
