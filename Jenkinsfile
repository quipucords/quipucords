node('f25-os') {
    pipeline{
        stages {
            stage('Install') {
            	echo "Installing lots of stuff"
		}
            stage('Build Docker Image') {
		echo "Building the docker image"
                touch targzfile
            }
	}
	post {
		success {
			echo "Success!!"
			archive targzfile
		}
	}
}
