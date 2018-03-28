node('f25-os') {
    stage('Install') {
        sh "sudo dnf -y install origin-clients nodejs"
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
    stage('Build Client') {
        dir('client') {
          sh "node -v"
          sh "npm -v"
          sh "sudo npm install -g n"
          sh "sudo n lts"
          sh "node -v"
          sh "npm -v"
          sh "npm install"
          sh "npm rebuild node-sass --force"
          sh "npm run build"
        }
    }
    stage('Build Docker Image') {
        sh "ls -lta"
        sh "cat Dockerfile"

        sh "git rev-parse HEAD > GIT_COMMIT"
        sh 'cat GIT_COMMIT'
        def commitHash = readFile('GIT_COMMIT').trim()

        def image_name = "quipucords:0.0.41"

        sh "sudo docker -D build --build-arg BUILD_COMMIT=$commitHash . -t $image_name"
        sh "sudo docker tag $image_name $DOCKER_REGISTRY/quipucords/$image_name"
        sh "sudo docker login -p $OPENSHIFT_TOKEN -u unused $DOCKER_REGISTRY"
        sh "sudo docker push $DOCKER_REGISTRY/quipucords/$image_name"

        def tarfile = "quipucords.0.0.41.tar"
        def targzfile = tarfile + ".gz"
        sh "sudo docker save -o $tarfile $image_name"
        sh "sudo chmod 755 $tarfile"
        sh "sudo gzip -f --best $tarfile"
        sh "sudo chmod 755 $targzfile"

        def install_tar = "quipucords.install.tar"
        def install_targzfile = install_tar + ".gz"
        sh "sudo tar -cvf $install_tar install/*"
        sh "sudo chmod 755 $install_tar"
        sh "sudo gzip -f --best $install_tar"
        sh "sudo chmod 755 $install_targzfile"

        archive targzfile
        archive install_targzfile

    }
}
