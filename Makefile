# Not really working as expected...

CURL := $(shell which curl 2>/dev/null)
UV := $(shell which uv 2>/dev/null)
CADDY := $(shell which caddy 2>/dev/null)
VENV := $(shell ls .venv 2>/dev/null)
ACTIVE := $(shell sudo systemctl is-active wasteman 2>/dev/null)

install-wasteman:
ifndef CURL
	sudo apt install curl -y
endif

ifndef UV
	curl -LsSf https://astral.sh/uv/install.sh | sh
endif

ifndef CADDY
	sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
	curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
	curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
	chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
	chmod o+r /etc/apt/sources.list.d/caddy-stable.list
	sudo apt update
	sudo apt install caddy
endif

ifndef VENV
	uv venv
	uv sync
endif

ifndef ACTIVE
	cp ./wasteman.service /etc/systemd/system \
	&& systemctl daemon-reload \
	&& systemctl enable wasteman \
	&& systemctl start wasteman
endif

	# Could cause problems with permissions...
	echo -e "\nimport $(pwd)/Caddyfile" >> /etc/caddy/Caddyfile
	caddy reload --config /etc/caddy/Caddyfile