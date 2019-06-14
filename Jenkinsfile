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
        sh "sudo dnf -y install origin-clients"
        sh "rpm -q docker"
        sh "which docker"
        sh "echo OPTIONS=\\'--log-driver=journald\\' > /tmp/docker.conf"
        sh "echo DOCKER_CERT_PATH=/etc/docker >> /tmp/docker.conf"
        sh "sudo cp /tmp/docker.conf /etc/sysconfig/docker"
        sh "cat /etc/sysconfig/docker"
        sh "sudo systemctl start docker"
        checkout scm
        sh "sleep 35s"
        sh "ps aux | grep docker"
        sh "sudo docker -v"
        sh "sudo setenforce 0"
    }
    stage('Copy UI into Server') {
        copyArtifacts filter: 'quipucords-ui-dist.tar.gz', fingerprintArtifacts: true, projectName: "qpc_${VERSION}_ui_distribution", selector: lastCompleted()
        sh "tar -xvf quipucords-ui-dist.tar.gz"
        sh "cp -rf dist/client quipucords/"
    	sh "cp -rf dist/templates quipucords/quipucords/"
        sh "rm -rf dist"
    }
    stage('Build Docker Image') {
        sh "echo { release_version : ${qpc_version} } >& ${version_json_file}"
    }
}
