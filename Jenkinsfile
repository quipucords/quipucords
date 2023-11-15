@Library("smqe-shared-lib@master") _

node("discovery_ci && fedora") {
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
