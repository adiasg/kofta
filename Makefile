deps:
	pip3 install apscheduler httpx flask pika

clean:
	rm -rf venv __pycache__
