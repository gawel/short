APP:=$(shell basename `pwd`)
HOSTNAME:=$(shell hostname)
HOST:=amandine

venv:
	python3 -m venv venv
	./venv/bin/pip install -e .

test:
	tox

serve: venv
	./venv/bin/$(APP) --serve

upgrade:
ifeq ($(HOSTNAME), $(HOST))
	git pull origin master
	~/apps/bin/circusctl restart $(APP)
else
	git push origin master
	ssh $(HOST) "cd ~/apps/$(APP) && make upgrade"

sync:
	scp $(HOST):~/.$(APP).json ~/.$(APP).json
endif

