def image_name = "quipucords:${BUILD_VERSION}"
def tarfile = "quipucords_server_image.tar"
def targzfile = "${tarfile}.gz"
def postgres_version = "9.6.10"
def postgres_image_name = "postgres:${postgres_version}"
def postgres_tarfile = "postgres.${postgres_version}.tar"
def postgres_dir = "postgres.${postgres_version}"
def postgres_targzfile = "postgres.${postgres_version}.tar.gz"
def postgres_license = "PostgreSQL_License.txt"
def rename_license = "${postgres_dir}/license.txt"
def release_info_file = "release_info.json"
def release_py_file = "release.py"
def release_py_full_path = "quipucords/quipucords/${release_py_file}"

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
        sh "ls -lta"
        sh "cat Dockerfile"

        sh "git rev-parse HEAD > GIT_COMMIT"
        sh 'cat GIT_COMMIT'
        def commitHash = readFile('GIT_COMMIT').trim()

        sh "sed -i s/BUILD_VERSION_PLACEHOLDER/${BUILD_VERSION}/g ${release_info_file}"
        sh "sed -i s/BUILD_VERSION_PLACEHOLDER/${BUILD_VERSION}/g ${release_py_full_path}"

        sh "sudo docker -D build --build-arg BUILD_COMMIT=$commitHash . -t $image_name"
        sh "sudo docker save -o $tarfile $image_name"
        sh "sudo chmod 755 $tarfile"
        sh "sudo gzip -f --best $tarfile"
        sh "sudo chmod 755 $targzfile"

        sh "sudo docker pull $postgres_image_name"
        sh "sudo docker save -o $postgres_tarfile $postgres_image_name"
        sh "sudo chmod 755 $postgres_tarfile"

        sh "mkdir $postgres_dir"
        sh "mv $postgres_tarfile $postgres_dir"
        sh "cp $postgres_license $rename_license"
        sh "tar -zcvf $postgres_targzfile $postgres_dir"
        sh "sudo chmod 775 $postgres_targzfile"

        archiveArtifacts release_info_file
        archiveArtifacts postgres_targzfile
        archiveArtifacts targzfile
    }
}
