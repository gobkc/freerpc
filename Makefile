build:
	rm -rf *.pyz
	python3 -m zipapp . -o freerpc.pyz -m "main:main"
	python3 freerpc.pyz
install:
	sudo apt update
	sudo apt install python3-grpcio python3-grpc-tools python3-protobuf
debug:
	GTK_DEBUG=interactive python3 main.py
