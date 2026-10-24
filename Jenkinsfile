pipeline {
    agent any

    environment {
        TODAY = '2026-10-12'
    }

    stages {
        stage('Install') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install -e . pytest pytest-cov ruff mypy
                '''
            }
        }
        stage('Lint') {
            steps {
                sh '. .venv/bin/activate && ruff check .'
            }
        }
        stage('Types') {
            steps {
                sh '. .venv/bin/activate && mypy src'
            }
        }
        stage('Test') {
            steps {
                sh '. .venv/bin/activate && pytest --cov=libraryhub --cov-fail-under=90'
            }
        }
        stage('Docker image') {
            steps {
                sh 'docker build -t libraryhub-mini:${BUILD_NUMBER} .'
            }
        }
    }
}