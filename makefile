uw-categories:
	@test $$(docker images -q visual-content-data) || make build
	@docker run -v $$(pwd):/app visual-content-data env START=$(START) STOP=$(STOP) TAG=$(TAG) python3 src/uw-categories.py

uw-deletion-requests:
	@test $$(docker images -q visual-content-data) || make build
	@docker run -v $$(pwd):/app visual-content-data env START=$(START) STOP=$(STOP) TAG=$(TAG) DAYS=$(DAYS) TEXT=$(TEXT) python3 src/uw-deletion-requests.py

build:
	docker build . -t visual-content-data

.PHONY: build
