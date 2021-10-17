# paths
PREFIX = /usr/local
MANPREFIX = ${PREFIX}/share/man

install: 
	mkdir -p ${DESTDIR}${PREFIX}/bin
	install -Dm755 pulsemeeter pmctl ${DESTDIR}${PREFIX}/bin
	install -Dm644 Interface.glade ${DESTDIR}${PREFIX}/share/doc/pulsemeeter/Interface.glade
	install -Dm644 LICENSE ${DESTDIR}${PREFIX}/share/licenses/pulsemeeter/LICENSE
	install -Dm644 pulsemeeter.desktop ${DESTDIR}/usr/share/applications/pulsemeeter.desktop
	for size in "192x192" "128x128" "96x96" "64x64" "48x48" "32x32" "24x24" "22x22" "20x20" "16x16" "8x8";	do \
		install -dm755 "${DESTDIR}${PREFIX}/share/icons/hicolor/$$size/apps"; \
		convert "Pulsemeeter.png" -strip -resize "$$size" "${DESTDIR}${PREFIX}/share/icons/hicolor/$$size/apps/Pulsemeeter.png"; \
	done
	#install -Dm644 README ${DESTDIR}${PREFIX}/share/doc/pulsemeeter/README
	#install -Dm644 pulsemeeter.1 ${DESTDIR}${MANPREFIX}/man1/pulsemeeter.1

uninstall:
	rm ${DESTDIR}${PREFIX}/bin/pulsemeeter
	rm ${DESTDIR}${PREFIX}/bin/pmctl 
	rm ${DESTDIR}/usr/share/applications/pulsemeeter.desktop
	rm -rf ${DESTDIR}${PREFIX}/share/doc/pulsemeeter
	rm -rf ${DESTDIR}${PREFIX}/share/licenses/pulsemeeter
	rm -rf ${DESTDIR}${PREFIX}/share/licenses/noisetorch-ladspa
	rm ${DESTDIR}${PREFIX}/lib/ladspa/rnnoise_ladspa.so
	for size in "192x192" "128x128" "96x96" "64x64" "48x48" "32x32" "24x24" "22x22" "20x20" "16x16" "8x8"; do \
		rm "${DESTDIR}${PREFIX}/share/icons/hicolor/$$size/apps/Pulsemeeter.png"; \
	done

clean: 
	rm -rf NoiseTorch
