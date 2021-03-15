SHELL=/bin/bash

.PHONY: all

all: build run

build:
	@docker build -t felipefrocha89/esufmg:crawler .

run: build
	@docker run -d --rm -v $$PWD:/app -w /app felipefrocha89/esufmg:crawler __init__.py

runa:
	@docker run -it --rm -v $$PWD:/app -w /app felipefrocha89/esufmg:crawler __init__.py

