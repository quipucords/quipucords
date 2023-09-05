@Library("smqe-shared-lib@mzalewsk/support-dsc-pr-fork") _

node("discovery_ci") {
    stage("Setup test environment") {
        echo "Setting up Quipucords PR tests"
        discoveryLib.setupCIEnv()
    }
    stage("Run tests") {
        discoveryLib.runTests()
    }
    stage("Archive artifacts") {
        discoveryLib.archiveArtifacts()
    }
}
