# Pulsemeeter ZIP install
.PHONY: zip install uninstall

PREFIX=/usr/local
BUILD_DIR=./buildzip
DIST_DIR=${BUILD_DIR}/dist
PKG_DIR=${BUILD_DIR}/pkg

all: zip

zip:
	@echo Removing old build files
	rm -rf ${BUILD_DIR}
	@echo Building source
	pip install . -t ${DIST_DIR}
	@echo Moving data files to package
	mkdir -p ${PKG_DIR}
	mv ${DIST_DIR}/bin ${PKG_DIR}
	mv ${DIST_DIR}/share ${PKG_DIR}
	@echo Deleting unnecessary files
	rm -rf ${DIST_DIR}/pydantic ${DIST_DIR}/pydantic_core ${DIST_DIR}/include ${DIST_DIR}/*.dist-info
	@echo Zipping package
	python -m zipapp ${DIST_DIR} -m "pulsemeeter.main:main" -o \
		${PKG_DIR}/bin/pulsemeeter -p '/usr/bin/env python3'

install: zip
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	install -Dm755 ${PKG_DIR}/bin/* $(DESTDIR)$(PREFIX)/bin
	install -Dm644 LICENSE ${DESTDIR}${PREFIX}/share/licenses/pulsemeeter/LICENSE
	install -Dm644 README.md ${DESTDIR}${PREFIX}/share/doc/pulsemeeter/README.md
	cp -r ${PKG_DIR}/share ${DESTDIR}${PREFIX}/

uninstall:
	rm -rf $(DESTDIR)$(PREFIX)/bin/pulsemeeter \
		$(DESTDIR)$(PREFIX)/bin/pmctl \
		${DESTDIR}${PREFIX}/share/licenses/pulsemeeter \
		${DESTDIR}${PREFIX}/share/doc/pulsemeeter \
		${DESTDIR}${PREFIX}/share/applications/pulsemeeter.desktop \
		${DESTDIR}${PREFIX}/share/locale/*/LC_MESSAGES/pulsemeeter.mo \
		${DESTDIR}${PREFIX}/share/icons/hicolor/*/apps/Pulsemeeter.png \

clean:
	rm -rf ${BUILD_DIR} ./build
