install:
	pip3 install apscheduler
	pip3 install httpx
	pip3 install flask
	pip3 install pika

clean:
	rm -rf venv __pycache__
