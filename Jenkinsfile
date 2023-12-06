@Library("smqe-shared-lib@master") _

properties([
    parameters([
        booleanParam(defaultValue: true, name: 'TEST_API'),
        booleanParam(defaultValue: true, name: 'TEST_CLI'),
        booleanParam(defaultValue: true, name: 'TEST_UI')
    ])
])

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
