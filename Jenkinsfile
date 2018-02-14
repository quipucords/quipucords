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
        checkout scm
        sh "sleep 35s"
        sh "ps aux | grep docker"
        sh "sudo docker -v"
        sh "sudo setenforce 0"
    }
    stage('Build Docker Image') {
        sh "ls -lta"
        sh "cat Dockerfile"
        sh "sudo docker -D build . -t quipucords:latest"
        sh "sudo docker tag quipucords:latest $DOCKER_REGISTRY/quipucords/quipucords:latest"
        sh "sudo docker login -p $OPENSHIFT_TOKEN -u unused $DOCKER_REGISTRY"
        sh "sudo docker push $DOCKER_REGISTRY/quipucords/quipucords:latest"
    }
}
