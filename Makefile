build:
	rm -rf *.pyz
	python3 -m zipapp . -o freerpc.pyz -m "main:main"
	python3 freerpc.pyz
debug:
	GTK_DEBUG=interactive python3 main.py
