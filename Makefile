setup-local: 
	@echo "Setting up development environment"
	# install requirements
	pip3 install -r requirements.txt

test:
	@echo "Running tests and building a test docker image"
	# install requirements
	pip3 install -r requirements.txt
	# run tests
	bash tests/run.sh

