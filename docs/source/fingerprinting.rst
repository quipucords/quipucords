Fingerprints and the Fingerprinting Process
-------------------------------------------
The Quipucords scan process is used to discover the systems in your IT infrastructure and to inspect and gather information about the nature and contents of those systems. A *system* is any entity that can be interrogated by the Quipucords inspection tasks through an SSH connection, vCenter Server data, or the Satellite API. Therefore, a system can be a machine, such as a physical or virtual machine, and it can also be a different type of entity, such as a container.

During a scan, information, or a collection of facts, about a system is gathered from a single source (such as a network source only) or multiple sources (such as a network source and satellite source). A *fact* is a single piece of data about a system. Facts are processed to create a summarized set of data for that system that is called a fingerprint. A *fingerprint* is a set of facts that identifies a unique system and the features on that system, such as the operating system, CPU architecture, number of CPUs and cores, the different products that are installed on that system, the entitlements that are in use on that system, and so on.

Fingerprinting data is generated when you run a scan job. The results are held in the database until you request a summary report for a scan. If you request a detailed report, you receive the raw facts for that scan without any fingerprinting. When you request a summary report, you receive the fingerprinting data that includes the results from the deduplication, merging, and post-processing processes. These processes include identifying installed products and versions from the raw facts, finding consumed entitlements, finding and merging duplicate instances of products from different sources, and finding products installed in nondefault locations, among other steps.

The following sections show example fingerprint data, describe the components of a fingerprint, and describe in more detail the process that is used to create the fingerprint.


Fingerprints
^^^^^^^^^^^^^^^^^^^
A fingerprint is composed of a set of facts about the system in addition to facts about products, entitlements, sources, and metadata. The following example shows fingerprint data. A fingerprint for a single system, even with very few Red Hat products installed on it, can be many lines. Therefore, only a partial fingerprint is used in this example. ::

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

The first several lines of a fingerprint show facts about the system. For example, the ``os_release`` fact describes the installed operating system and release. For each system fact, there is a corresponding entry in the ``metadata`` section of the fingerprint that identifies the original source of that system fact.

The fingerprint also lists the consumed entitlements for that system in the ``entitlements`` section. Each entitlement in the list has a name, ID, and metadata that describes the original source of that fact. In the example fingerprint, the system has the ``Satellite Tools 6.3`` entitlement.

Next, the fingerprint lists the installed products in the ``products`` section. A product has a name, version, presence, and metadata field. Because the presence field shows ``absent`` as the value for JBoss EAP, the system in this example does not have JBoss EAP installed.

Lastly, the fingerprint lists the sources that contain this system in the ``sources`` section. A system can be contained in more than one source. For example, for a scan that includes both a network source and a satellite source, a single system can be found in both parts of the scan.


System Deduplication and Merging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can gather system information by using one or more of the following types of sources for a scan:

- network
- vcenter
- satellite

A single system can be found in multiple sources during a scan. For example, a virtual machine on vCenter Server could be running a Red Hat Enterprise Linux operating system installation that is also managed by Satellite. If you construct a scan that contains a vcenter, satellite, and network source, then that single system is reported by all three vcenter, satellite, and network sources during the scan.

To resolve this issue and build an accurate fingerprint, Quipucords feeds unprocessed system facts from the scan into a fingerprint engine. The fingerprint engine matches and merges data for systems that are found in more than one source by using the deduplication and merge processes.

Deduplication of Systems
~~~~~~~~~~~~~~~~~~~~~~~~
Quipucords uses specific facts about a system to identify duplicate systems. The following phases use these specific facts to remove duplicate systems during the deduplication process:

1. All systems from network sources are combined into a single network system set. Systems are considered to be duplicates if they have the same value for the ``subscription_manager_id`` or ``bios_uuid`` facts.
2. All systems from vcenter sources are combined into a single vcenter system set. Systems are considered to be duplicates if they have the same value for the ``vm_uuid`` fact.
3. All systems from satellite sources are combined into a single satellite system set. Systems are considered to be duplicates if they have the same value for the ``subscription_manager_id`` fact.
4. The network system set is merged with the satellite system set to form a single network-satellite system set. Systems are considered to be duplicates if they have the same value for the ``subscription_manager_id`` fact or matching MAC address values in the ``mac_addresses`` fact.
5. The network-satellite system set is merged with the vcenter system set to form the complete system set. Systems are considered to be duplicates if they have matching MAC address values in the ``mac_addresses`` fact or if the vcenter value for the ``vm_uuid`` fact matches the network value for the ``bios_uuid`` fact.

Merging Systems
~~~~~~~~~~~~~~~
After Quipucords determines that two systems are duplicates, it performs a merge. The merged system has a union of system facts from each source. When Quipucords merges a fact that appears in both systems, it uses the following order of precedence to merge the fact, from highest to lowest:

1. network
2. satellite
3. vcenter

A system fingerprint contains a ``metadata`` dictionary that captures the original source of each fact for that system.


Post Processing
~~~~~~~~~~~~~~~
After deduplication and merging are complete, there is a post-processing phase that creates derived system facts. A *derived system fact* is a fact that generated from the evaluation of more than one system fact. The majority of derived system facts are related to product identification data, such as the presence of a specific product and its version. The following information shows how the derived system fact ``system_creation_date`` is created.

System Creation Date
++++++++++++++++++++
The ``system_creation_date`` fact is a derived system fact that contains the real system creation time. The value for this fact is determined by the evaluation of the following facts. The value for each fact is examined in the following order of precedence, with the order of precedence determined by the accuracy of the match to the real system creation time. The highest non-empty value is used to determine the value of the ``system_creation_date`` derived system fact.

1. date_machine_id
2. registration_time
3. date_anaconda_log
4. date_filesystem_create
5. date_yum_history
