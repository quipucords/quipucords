pipeline {
    agent { label 'f28-os' }

    environment {
        qpc_version = "${params.version_name}"
        image_name = "quipucords:${qpc_version}"
        tarfile = "quipucords_server_image.tar"
        targzfile = "${tarfile}.gz"
        postgres_version = "9.6.10"
        postgres_image_name = "postgres:${postgres_version}"
        postgres_tarfile = "postgres.${postgres_version}.tar"
        postgres_dir = "postgres.${postgres_version}"
        postgres_targzfile = "postgres.${postgres_version}.tar.gz"
        postgres_license = "PostgreSQL_License.txt"
        rename_license = "${postgres_dir}/license.txt"
    }

parameters {
    string(defaultValue: "master", description: 'What version?', name: 'version_name')
    choice(choices: ['branch', 'tag'], description: "Branch or Tag?", name: 'version_type')
}

stages {
    stage('Build Info') {
        steps {
            echo "Version: ${params.version_name}\nVersion Type: ${params.version_type}\nCommit: ${env.GIT_COMMIT}"
        }
    }
    stage('Install') {
        steps {
            sh "sudo dnf -y install origin-clients"
            sh "rpm -q docker"
            sh "which docker"
            sh "echo OPTIONS=\\'--log-driver=journald\\' > /tmp/docker.conf"
            sh "echo DOCKER_CERT_PATH=/etc/docker >> /tmp/docker.conf"
            sh "sudo cp /tmp/docker.conf /etc/sysconfig/docker"
            sh "cat /etc/sysconfig/docker"
            sh "sudo systemctl start docker"

            // checkout scm
            script {
                if ("${params.version_type}" == 'branch') {
                    echo "Checkout Branch"
                    checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: "${params.version_name}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[url: "${env.GIT_URL}"]]]
                }
                if ("${params.version_type}" == 'tag') {
                    echo "Checkout Tag"
                    checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: "refs/tags/${params.version_name}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[url: "${env.GIT_URL}"]]]
                }
              }

            sh "sleep 35s"
            sh "ps aux | grep docker"
            sh "sudo docker -v"
            sh "sudo setenforce 0"
        }
    }
    stage('Copy UI into Server') {
        steps {
            copyArtifacts filter: 'quipucords-ui.*.tar.gz', fingerprintArtifacts: true, projectName: "quipucords-ui-build-job", selector: lastCompleted()
            sh "tar -xvf quipucords-ui.*.tar.gz"
            sh "ls -lah"
            sh "cp -rf dist/client quipucords/"
        	sh "cp -rf dist/templates quipucords/quipucords/"
            sh "rm -rf dist"
        }
    }
    stage('Build Docker Image') {
        steps {
            sh "ls -lta"
            sh "ls -lta quipucords"
            sh "cat Dockerfile"

            sh "git rev-parse HEAD > GIT_COMMIT"
            sh 'cat GIT_COMMIT'

            sh "sudo docker -D build --build-arg BUILD_COMMIT=`cat GIT_COMMIT` . -t $image_name"
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

            archiveArtifacts postgres_targzfile
            archiveArtifacts targzfile
        }
    }
}
}
