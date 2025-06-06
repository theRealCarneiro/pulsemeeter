#!/bin/sh

for file in src/pulsemeeter/locale/*/; do
	# echo $file
	msgfmt ${file}/LC_MESSAGES/pulsemeeter.po -o ${file}/LC_MESSAGES/pulsemeeter.mo
done
