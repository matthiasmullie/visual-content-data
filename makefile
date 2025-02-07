uw-categories:
	test $$(docker images -q visual-content-data) || make build
	docker run -v $$(pwd):/app visual-content-data env START=$(START) env STOP=$(STOP) TAG=$(TAG) python3 src/uw-categories.py

build:
	docker build . -t visual-content-data

.PHONY: build
