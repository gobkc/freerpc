build:
	rm -rf *.pyz
	python3 -m zipapp . -o freerpc.pyz -m "main:main"
