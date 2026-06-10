PKG        := freerpc
VERSION    := 0.1.0
ARCH       := all
MAINTAINER := xiong <xiong@localhost>

DEBROOT := build/$(PKG)_$(VERSION)_$(ARCH)
APPDIR  := $(DEBROOT)/usr/share/freerpc

build:
	rm -rf *.pyz
	python3 -m zipapp . -o freerpc.pyz -m "main:main" -p "/usr/bin/env python3"
	python3 freerpc.pyz

install:
	sudo apt update
	sudo apt install python3-gi gir1.2-gtk-4.0 python3-grpcio python3-protobuf protobuf-compiler protobuf-compiler-grpc

debug:
	GTK_DEBUG=interactive python3 main.py

deb:
	rm -rf $(DEBROOT)
	mkdir -p $(APPDIR) $(DEBROOT)/usr/bin $(DEBROOT)/DEBIAN \
		$(DEBROOT)/usr/share/applications \
		$(DEBROOT)/usr/share/icons/hicolor/scalable/apps
	cp -r app context handlers services ui utils styles main.py logo.svg $(APPDIR)/
	find $(APPDIR) -name __pycache__ -type d -prune -exec rm -rf {} +
	printf '#!/bin/sh\ncd /usr/share/freerpc\nexec python3 main.py "$$@"\n' > $(DEBROOT)/usr/bin/freerpc
	chmod 755 $(DEBROOT)/usr/bin/freerpc
	cp logo.svg $(DEBROOT)/usr/share/icons/hicolor/scalable/apps/freerpc.svg
	printf '[Desktop Entry]\nType=Application\nName=FreeRPC\nComment=Dynamic gRPC client\nExec=freerpc\nIcon=freerpc\nCategories=Development;\nTerminal=false\n' > $(DEBROOT)/usr/share/applications/freerpc.desktop
	printf 'Package: %s\nVersion: %s\nSection: devel\nPriority: optional\nArchitecture: %s\nDepends: python3, python3-gi, gir1.2-gtk-4.0, python3-grpcio, python3-protobuf, protobuf-compiler, protobuf-compiler-grpc\nMaintainer: %s\nDescription: Dynamic gRPC GUI client\n A GTK4 desktop client for invoking gRPC services from .proto files.\n' \
		"$(PKG)" "$(VERSION)" "$(ARCH)" "$(MAINTAINER)" > $(DEBROOT)/DEBIAN/control
	dpkg-deb --build --root-owner-group $(DEBROOT)
	@echo "Built $(DEBROOT).deb"

clean:
	rm -rf build *.pyz

.PHONY: build install debug deb clean
