node('f25-os') {
    stage('Install') {
        sh "sudo dnf -y install origin-clients"
        sh "which oc"
        sh "oc login --insecure-skip-tls-verify --token $OPENSHIFT_TOKEN $OPHENSHIFT_LOGIN_URL"
        sh "oc project quipucords"
        sh "rpm -q docker"
        sh "which docker"
        sh "echo OPTIONS=\\'--log-driver=journald\\' > /tmp/docker.conf"
        sh "echo DOCKER_CERT_PATH=/etc/docker >> /tmp/docker.conf"
        sh "echo INSECURE_REGISTRY=\\'--insecure-registry $DOCKER_REGISTRY\\' >> /tmp/docker.conf"
        sh "sudo cp /tmp/docker.conf /etc/sysconfig/docker"
        sh "cat /etc/sysconfig/docker"
        sh "sudo systemctl start docker"
        sh "sleep 35s"
        sh "ps aux | grep docker"
        sh "sudo docker -v"
        sh "sudo setenforce 0"
    }
    stage('Build Docker Image') {
        sh "git rev-parse HEAD > GIT_COMMIT"
        sh 'cat GIT_COMMIT'
        def commitHash = readFile('GIT_COMMIT').trim()

        sh "ls -lta"
        sh "cat Dockerfile"
        sh "sudo docker -D build . -t quipucords:beta"

        //sh "sudo docker tag quipucords:beta $DOCKER_REGISTRY/quipucords/quipucords:beta"
        //sh "sudo docker login -p $OPENSHIFT_TOKEN -u unused $DOCKER_REGISTRY"
        //sh "sudo docker push $DOCKER_REGISTRY/quipucords/quipucords:beta"

        def tarfile = "quipucords.beta." + commitHash + ".tar"
        def targzfile = tarfile + ".gz"
        sh "sudo docker save -o $tarfile quipucords:beta"
        sh "sudo gzip --best $tarfile"

        archiveArtifacts artifacts: targzfile
    }
}
