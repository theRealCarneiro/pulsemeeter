# paths
PREFIX = /usr/local
MANPREFIX = ${PREFIX}/share/man

install:
	mkdir -p ${DESTDIR}${PREFIX}/bin
	install -Dm755 pulsemeeter pmctl ${DESTDIR}${PREFIX}/bin
	install -Dm644 Interface.glade ${DESTDIR}${PREFIX}/share/doc/pulsemeeter/Interface.glade
	install -Dm644 LICENSE ${DESTDIR}${PREFIX}/share/licenses/pulsemeeter/LICENSE
	install -Dm644 pulsemeeter.desktop ${DESTDIR}/usr/share/applications/pulsemeeter.desktop
	#install -Dm644 README ${DESTDIR}${PREFIX}/share/doc/pulsemeeter/README
	#install -Dm644 pulsemeeter.1 ${DESTDIR}${MANPREFIX}/man1/pulsemeeter.1

uninstall:
	rm ${DESTDIR}${PREFIX}/bin/pulsemeeter
	rm ${DESTDIR}${PREFIX}/bin/pmctl 
	rm -rf ${DESTDIR}${PREFIX}/share/doc/pulsemeeter
	rm -rf ${DESTDIR}${PREFIX}/share/licenses/pulsemeeter
	rm ${DESTDIR}/usr/share/applications/pulsemeeter.desktop
