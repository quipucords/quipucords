@Library("smqe-shared-lib@master") _

def agents = [:]
agents["failFast"] = false

["fedora", "rhel8", "rhel9", "rhel10"].each { distro_label ->
    agents[distro_label] = {
        node("discovery_ci && ${distro_label}") {
            timestamps {
                stage("[${distro_label}] Setup test environment") {
                    echo "Setting up Quipucords PR tests"
                    discoveryLib.setupCIEnv()
                }
                stage("[${distro_label}] Run tests") {
                    discoveryLib.runTests()
                }
                stage("[${distro_label}] Archive artifacts") {
                    discoveryLib.archiveArtifacts()
                }
            }
        }
    }
}

parallel agents
