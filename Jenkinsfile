def qpc_version = "master"
def image_name = "quipucords:${qpc_version}"
def tarfile = "quipucords.${qpc_version}.tar"
def targzfile = "${tarfile}.gz"
def install_tar = "quipucords.install.tar"
def install_targzfile = "${install_tar}.gz"


def startQPCServer = {
    sh """\
    sudo docker run --name qpc-db -e POSTGRES_PASSWORD=password -d postgres:9.6.10
    sudo docker run -d -p "443:443" --link qpc-db:qpc-link \\
        -e QPC_DBMS_HOST=qpc-db \\
        -e QPC_DBMS_PASSWORD=password \\
        -v /tmp:/tmp \
        -v /home/jenkins/.ssh:/home/jenkins/.ssh \\
        -v \${PWD}/log:/var/log \\
        -i ${image_name}
    """.stripIndent()

    sh '''\
    for i in {1..30}; do
        SERVER_ID="$(curl -ks https://localhost:443/api/v1/status/ | grep server_id || true)"

        if [ "${SERVER_ID}" ]; then
            break
        fi

        if [ $i -eq 30 ]; then
            echo "Server took too long to start"
            exit 1
        fi

        sleep 1
    done
    '''.stripIndent()
}


def configureDocker = {
    sh """\
    echo "OPTIONS=--log-driver=journald" > docker.conf
    echo "DOCKER_CERT_PATH=/etc/docker" >> docker.conf
    echo "INSECURE_REGISTRY=\\"--insecure-registry \${DOCKER_REGISTRY}\\"" >> docker.conf
    sudo cp docker.conf /etc/sysconfig/docker
    sudo systemctl start docker
    sudo docker load -i ${targzfile}
    # make log dir to save server logs
    mkdir -p log
    """.stripIndent()
}

def installQpcClient() {
    sh '''\
    sudo wget -O /etc/yum.repos.d/chambridge-qpc-fedora-28.repo https://copr.fedorainfracloud.org/coprs/chambridge/qpc/repo/fedora-28/chambridge-qpc-fedora-28.repo
    sudo dnf -y install qpc
    '''.stripIndent()
}

def setupScanUsers() {
    dir('ci') {
        git 'https://github.com/quipucords/ci.git'
    }

    sshagent(['390bdc1f-73c6-457e-81de-9e794478e0e']) {
        withCredentials([file(credentialsId: '50dc19ce-555f-422c-af38-3b5ede422bb4', variable: 'ID_JENKINS_RSA_PUB')]) {
            sh 'sudo dnf -y install ansible'

            sh '''\
            cat > jenkins-slave-hosts <<EOF
            [jenkins-slave]
            ${OPENSTACK_PUBLIC_IP}

            [jenkins-slave:vars]
            ansible_user=jenkins
            ansible_ssh_extra_args=-o StrictHostKeyChecking=no
            ssh_public_key_file=$(cat ${ID_JENKINS_RSA_PUB})
            EOF
            '''.stripIndent()

            sh 'ansible-playbook -b -i jenkins-slave-hosts ci/ansible/sonar-setup-scan-users.yaml'
        }
    }
}


def setupCamayoc() {
    dir('camayoc') {
        git 'https://github.com/quipucords/camayoc.git'
    }

    sh '''\
    sudo pip install ./camayoc[dev]
    cp camayoc/pytest.ini .
    '''.stripIndent()

    withCredentials([file(credentialsId: '4c692211-c5e1-4354-8e1b-b9d0276c29d9', variable: 'ID_JENKINS_RSA')]) {
        sh '''\
        mkdir -p /home/jenkins/.ssh
        cp "${ID_JENKINS_RSA}" /home/jenkins/.ssh/id_rsa
        chmod 0600 /home/jenkins/.ssh/id_rsa
        '''.stripIndent()
    }

    configFileProvider([configFile(fileId: '62cf0ccc-220e-4177-9eab-f39701bff8d7', targetLocation: 'camayoc/config.yaml')]) {
        sh '''\
        sed -i "s/{jenkins_slave_ip}/${OPENSTACK_PUBLIC_IP}/" camayoc/config.yaml
        '''.stripIndent()

    }
}


node('f28-os') {
    stage('Install') {
        sh "sudo dnf -y install nodejs"
        sh "node -v"
        sh "npm -v"
        sh "echo OPTIONS=\\'--log-driver=journald\\' > /tmp/docker.conf"
        sh "echo DOCKER_CERT_PATH=/etc/docker >> /tmp/docker.conf"
        sh "echo INSECURE_REGISTRY=\\'--insecure-registry $DOCKER_REGISTRY\\' >> /tmp/docker.conf"
        sh "sudo cp /tmp/docker.conf /etc/sysconfig/docker"
        sh "sudo systemctl start docker"
        sh "sudo setenforce 0"
        git 'https://github.com/quipucords/quipucords.git'
    }
    stage('Build UI') {

        dir('client') {
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
        copyArtifacts filter: "${targzfile}", fingerprintArtifacts: true, optional: true, projectName: 'qpc-master', selector: lastCompleted()

        sh """\
        if [ -f ${targzfile} ]; then
            sudo docker load -i ${targzfile}
        fi
        """.stripIndent()

        sh "ls -lta"
        sh "cat Dockerfile"

        sh "git rev-parse HEAD > GIT_COMMIT"
        sh 'cat GIT_COMMIT'
        def commitHash = readFile('GIT_COMMIT').trim()

        sh "sudo docker -D build --build-arg BUILD_COMMIT=$commitHash --cache-from=${image_name} -t ${image_name} ."

        sh "sudo docker save -o $tarfile $image_name"
        sh "sudo chmod 755 $tarfile"
        sh "sudo gzip -f --best $tarfile"
        sh "sudo chmod 755 $targzfile"

        sh "sudo tar -cvf $install_tar install/*"
        sh "sudo chmod 755 $install_tar"
        sh "sudo gzip -f --best $install_tar"
        sh "sudo chmod 755 $install_targzfile"

        archive targzfile
        archive install_targzfile

        build job: 'qpc-master-test-install', wait: false
    }

    stage('Setup Integration Tests') {
        configureDocker()
        installQpcClient()
        setupScanUsers()
        setupCamayoc()
    }

    stage('Test API') {
        startQPCServer()

        sshagent(['390bdc1f-73c6-457e-81de-9e794478e0e']) {
            sh '''
            export XDG_CONFIG_HOME=$PWD

            set +e
            py.test -c pytest.ini -l -ra -s -vvv --junit-xml api-junit.xml --rootdir camayoc/camayoc/tests/qpc camayoc/camayoc/tests/qpc/api
            set -e

            sudo docker rm $(sudo docker stop $(sudo docker ps -aq))
            tar -cvzf test-api-logs.tar.gz log
            sudo rm -rf log
            '''.stripIndent()
        }

        archiveArtifacts 'test-api-logs.tar.gz'

        junit 'api-junit.xml'
    }

    stage('Test CLI') {
        startQPCServer()

        sshagent(['390bdc1f-73c6-457e-81de-9e794478e0e']) {
            sh '''\
            export XDG_CONFIG_HOME=$PWD

            set +e
            py.test -c pytest.ini -l -ra -vvv --junit-xml cli-junit.xml --rootdir camayoc/camayoc/tests/qpc camayoc/camayoc/tests/qpc/cli
            set -e

            sudo docker rm $(sudo docker stop $(sudo docker ps -aq))
            tar -cvzf test-cli-logs.tar.gz log
            sudo rm -rf log
            '''.stripIndent()
        }

        archiveArtifacts 'test-cli-logs.tar.gz'

        junit 'cli-junit.xml'
    }

    stage('Test UI Chrome') {
        startQPCServer()

        sshagent(['390bdc1f-73c6-457e-81de-9e794478e0e']) {
            sh 'sudo docker run --net="host" -d -p 4444:4444 -v /dev/shm:/dev/shm:z -v /tmp:/tmp:z selenium/standalone-chrome-debug:3.14.0-arsenic'

            sh '''\
            export XDG_CONFIG_HOME=$PWD
            export SELENIUM_DRIVER=chrome

            set +e
            py.test -c pytest.ini -l -ra -vvv --junit-prefix chrome --junit-xml ui-chrome-junit.xml --rootdir camayoc/camayoc/tests/qpc camayoc/camayoc/tests/qpc/ui
            set -e

            sudo docker rm $(sudo docker stop $(sudo docker ps -aq))
            tar -cvzf test-ui-chrome-logs.tar.gz log
            sudo rm -rf log
            '''.stripIndent()
        }

        archiveArtifacts 'test-ui-chrome-logs.tar.gz'

        junit 'ui-chrome-junit.xml'
    }

    stage('Test UI Firefox') {
        startQPCServer()

        sshagent(['390bdc1f-73c6-457e-81de-9e794478e0e']) {
            sh 'sudo docker run --net="host" -d -p 4444:4444 -v /dev/shm:/dev/shm:z -v /tmp:/tmp:z selenium/standalone-firefox-debug:3.14.0-arsenic'

            sh '''\
            export XDG_CONFIG_HOME=$PWD
            export SELENIUM_DRIVER=firefox

            set +e
            py.test -c pytest.ini -l -ra -vvv --junit-prefix firefox --junit-xml ui-firefox-junit.xml --rootdir camayoc/camayoc/tests/qpc camayoc/camayoc/tests/qpc/ui
            set -e

            sudo docker rm $(sudo docker stop $(sudo docker ps -aq))
            tar -cvzf test-ui-firefox-logs.tar.gz log
            sudo rm -rf log
            '''.stripIndent()
        }

        archiveArtifacts 'test-ui-firefox-logs.tar.gz'

        junit 'ui-firefox-junit.xml'
    }
}
