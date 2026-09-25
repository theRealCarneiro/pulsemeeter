# Pulsemeeter ZIP install
.PHONY: all zip check-deps install uninstall clean
.NOTPARALLEL:

PREFIX=/usr/local
PYTHON=python3
BUILD_DIR=./buildzip
DIST_DIR=${BUILD_DIR}/dist
PKG_DIR=${BUILD_DIR}/pkg

# Skip depends if not building for install on this machine
ifneq ($(DESTDIR),)
SKIP_DEP_CHECK := 1
endif

all: zip

zip:
	@echo Removing old build files
	rm -rf ${BUILD_DIR}
	@echo Building source
	${PYTHON} -m pip install . pulsectl pulsectl-asyncio -t ${DIST_DIR} --no-deps
	@echo Moving data files to package
	mkdir -p ${PKG_DIR}
	mv ${DIST_DIR}/bin ${PKG_DIR}
	mv ${DIST_DIR}/share ${PKG_DIR}
	@echo Deleting unnecessary files
	rm -rf ${DIST_DIR}/include ${DIST_DIR}/*.dist-info
	@echo Zipping package
	${PYTHON} -m zipapp ${DIST_DIR} -m "pulsemeeter.main:main" -o \
		${PKG_DIR}/bin/pulsemeeter -p '/usr/bin/env ${PYTHON}'

check-deps:
ifeq ($(SKIP_DEP_CHECK),)
	@${PYTHON} -c "import pydantic, gi; gi.require_version('Gtk', '4.0')" || { \
		echo; \
		echo "pulsemeeter needs pydantic, PyGObject and GTK 4 on ${PYTHON}."; \
		echo "The zipapp cannot bundle them. Install them with your package manager:"; \
		echo "  Debian/Ubuntu  sudo apt install python3-pydantic python3-gi gir1.2-gtk-4.0"; \
		echo "  Arch           sudo pacman -S --needed python-pydantic python-gobject gtk4"; \
		echo "  Fedora         sudo dnf install python3-pydantic python3-gobject gtk4"; \
		echo; \
		echo "To install anyway: make install SKIP_DEP_CHECK=1"; \
		exit 1; \
	}
endif

install: check-deps zip
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	install -Dm755 ${PKG_DIR}/bin/* $(DESTDIR)$(PREFIX)/bin
	install -Dm644 LICENSE ${DESTDIR}${PREFIX}/share/licenses/pulsemeeter/LICENSE
	install -Dm644 README.md ${DESTDIR}${PREFIX}/share/doc/pulsemeeter/README.md
	cp -r ${PKG_DIR}/share ${DESTDIR}${PREFIX}/

uninstall:
	# pmctl is legacy; keeping for cleanup
	rm -rf $(DESTDIR)$(PREFIX)/bin/pulsemeeter \
		$(DESTDIR)$(PREFIX)/bin/pmctl \
		${DESTDIR}${PREFIX}/share/licenses/pulsemeeter \
		${DESTDIR}${PREFIX}/share/doc/pulsemeeter \
		${DESTDIR}${PREFIX}/share/applications/pulsemeeter.desktop \
		${DESTDIR}${PREFIX}/share/applications/org.pulsemeeter.pulsemeeter.desktop \
		${DESTDIR}${PREFIX}/share/locale/*/LC_MESSAGES/pulsemeeter.mo \
		${DESTDIR}${PREFIX}/share/icons/hicolor/*/apps/Pulsemeeter.png \

clean:
	rm -rf ${BUILD_DIR} ./build
