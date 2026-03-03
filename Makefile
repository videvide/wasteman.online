wasteman:
	# curl
	if [ $(which curl) = "" ]; then
		sudo apt install curl -y 
	fi

	# uv
	if [ $(which uv) = "" ]; then
		wget -qO- https://astral.sh/uv/install.sh | sh
	fi

	# Caddy
	if [ $(which caddy) = "" ]; then
		sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
		curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
		curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
		chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
		chmod o+r /etc/apt/sources.list.d/caddy-stable.list
		sudo apt update
		sudo apt install caddy
	fi

	# Install uv venv
	uv venv
	uv sync

	# Install systemd service
	sudo cp ./wasteman.service /etc/systemd/system
	# Start the service
	sudo systemctl daemon-reload && sudo systemctl enable wasteman && sudo systemctl start wasteman

	# Include project Caddyfile in main Caddyfile (Could cause problems with permissions)
	echo -e "\nimport $(pwd)/Caddyfile" >> /etc/caddy/Caddyfile
	caddy reload --config /etc/caddy/Caddyfile