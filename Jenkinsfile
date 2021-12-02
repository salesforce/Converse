pipeline {
    agent any
    stages {
        stage('UnitTest') {
            steps {
                echo 'Run UnitTest...'
                sh '''
                export PATH=$WORKSPACE/venv/bin:/usr/local/bin:$PATH
                if [ ! -d "venv" ]; then
                       virtualenv --no-site-packages venv --python=/opt/conda/bin/python3.7
                fi
                . venv/bin/activate
                pip install -r ./requirements.txt 
                PYTHONPATH=. python -m unittest discover  -s test_files -p 'Test*.py'
                deactivate
                '''
            }
        }
    }

    post {
        always {
            script {
                COMMITTER = sh(script: "git show -s --pretty=%an", returnStdout: true).trim()
                SHA = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
            }
            slackSend (color:"#FF0000", 
              message: "Job: ${env.JOB_NAME}\n Branch: ${GIT_BRANCH}\n SHA:${SHA}\n Committer: ${COMMITTER}\n Status: *${currentBuild.currentResult}*\n Check ${env.BUILD_URL} for details.")
        }
    }
}
