#!/bin/sh

ho="$(iniparser hardware_output $HOME/Bibliotecas/Projects/pulsemeeter/config.ini)"
hon="$(echo "$ho" | wc -l)"
eval $ho

hi="$(iniparser hardware_input $HOME/Bibliotecas/Projects/pulsemeeter/config.ini)"
hin="$(echo "$hi" | wc -l)"
eval $hi

vi="$(iniparser virtual_input $HOME/Bibliotecas/Projects/pulsemeeter/config.ini)"
vin="$(echo "$vi" | wc -l)"
eval $vi

vo="$(iniparser virtual_output $HOME/Bibliotecas/Projects/pulsemeeter/config.ini)"
von="$(echo "$vo" | wc -l)"
eval $vo


init (){
	for i in $(seq 1 $vin); do
		eval "j="\$vi$i""
		if ! get sink vi$i >/dev/null; then
			pactl load-module module-null-sink sink_name=$j sink_properties="device.description="$j""
			pacmd update-sink-proplist $j device.description=$j
		fi
	done

	for i in $(seq 1 $von); do
		eval "j="\$b$i""
		if ! get "source" b$i >/dev/null; then
			pactl load-module module-null-sink sink_name=$j"_sink"
			pacmd update-sink-proplist $j"_sink" device.description=$j"_sink"
			pactl load-module module-remap-source source_name=$j master=$j"_sink.monitor"
			pacmd update-source-proplist $j device.description=$j
		fi
	done
}


connect (){

	eval "vi="\$$1""
	eval "ho="\$$2""

	[ -z "$vi" -o -z "$ho" ] && exit
	pacmd list-modules | grep -B 2 "$ho source=$vi" >/dev/null || \
		pactl load-module module-loopback sink=$ho source=$vi
}

disconnect (){
	eval "vi="\$$1""
	eval "ho="\$$2""

	[ -z "$vi" -o -z "$ho" ] && exit
	index="$(pacmd list-modules | grep -B 2 "$ho source=$vi" | grep index | sed 's/[^0-9]*//g')"
		[ -z $index ] || pactl unload-module $index
}

remove (){
	eval "vi="\$$1""
	eval "ho="\$$2""
	index="$(pacmd list-modules | grep -B 2 "$vi>" | grep index | sed 's/[^0-9]*//g')"
	[ -z $index ] || pactl unload-module $index
}

volume (){
	eval "vi="\$$2""
	[ -z $vi ] && exit
	pactl set-$1-volume $vi $3%
}

get (){
		eval "j="\$$2""
		[ -z $j ] && exit
		if [ "$1" = "sink" ]; then
			aux=$(pacmd list-sinks | grep -A 40 $j | grep alsa.card.name | sed 's/.*= //g; s/"//g')
		else
			aux=$(pacmd list-sources | grep -A 37 $j | grep alsa.card_name | sed 's/.*= //g; s/"//g')
		fi

		if [ -z "$aux" ]; then 
			eval "echo "\$$2""
		else
			echo $aux
		fi

}

case $1 in
	"init")
		init
	;;
	"connect") 
		connect $2 $3 $4
	;;
	"disconnect")
		disconnect $2 $3 $4
	;;
	"remove")
		remove $2 $3
	;;
	"volume")
		volume $2 $3 $4
	;;
	"get")
		get $2 $3
	;;
	"*") echo "command not found";;
esac
