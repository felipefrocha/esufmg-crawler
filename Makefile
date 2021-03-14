SHELL=/bin/bash
.SHELLFLAGS=-ev

build:
	@docker build -t felipefrocha89/esufmg:crawler . 

run: build
	@docker run -it --rm -v $PWD:/app -w /app felipefrocha89/esufmg:crawler __init__.py

all: build run

.PHONY: all