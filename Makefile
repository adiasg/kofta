install:
	python3 -m venv venv
	. venv/bin/activate
	pip3 install redis
	pip3 install apscheduler
	pip3 install httpx
	pip3 install flask

clean:
	rm -rf venv __pycache__
