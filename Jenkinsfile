def qpc_version = "0.9.0"
def image_name = "quipucords:${qpc_version}"
def tarfile = "quipucords_server_image.tar"
def targzfile = "${tarfile}.gz"
def version_json_file = "version.json"
def postgres_version = "9.6.10"
def postgres_image_name = "postgres:${postgres_version}"
def postgres_tarfile = "postgres.${postgres_version}.tar"
def postgres_dir = "postgres.${postgres_version}"
def postgres_targzfile = "postgres.${postgres_version}.tar.gz"
def postgres_license = "PostgreSQL_License.txt"
def rename_license = "${postgres_dir}/license.txt"

node('f28-os') {
    stage('Install') {
        checkout scm
        sh "sudo setenforce 0"
    }
    stage('Copy UI into Server') {
        copyArtifacts filter: 'quipucords-ui-dist.tar.gz', fingerprintArtifacts: true, projectName: "qpc_${VERSION}_ui_distribution", selector: lastCompleted()
    }
    stage('Build Docker Image') {
        sh "echo { release_version : ${qpc_version} } >& ${version_json_file}"
        archiveArtifacts version_json_file

    }
}
