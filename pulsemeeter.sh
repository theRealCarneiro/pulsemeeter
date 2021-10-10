#!/bin/env bash

init (){
	case $1 in
		"sink")
			sink=$2
			pactl list sinks short | grep $sink && exit
			pactl load-module module-null-sink sink_name=$sink sink_properties="device.description="$sink""
			pacmd update-sink-proplist $sink device.description=$sink
		;;
		"source")
			source=$2
			pactl list sources short | grep $source && exit
			pactl load-module module-null-sink sink_name=$source"_sink"
			pacmd update-sink-proplist $source"_sink" device.description=$source"_sink"
			pactl load-module module-remap-source source_name=$source master=$source"_sink.monitor"
			pacmd update-source-proplist $source device.description=$source
		;;
	esac
	
}

connect (){
	vi=$1
	ho=$2

	[ -z "$vi" -o -z "$ho" ] && exit
	pacmd list-modules | grep -B 2 "$ho source=$vi" >/dev/null || \
		pactl load-module module-loopback sink=$ho source=$vi
}

disconnect (){
	vi=$1
	ho=$2

	[ -z "$vi" -o -z "$ho" ] && exit
	index="$(pacmd list-modules | grep -B 2 "$ho source=$vi" | grep index | sed 's/[^0-9]*//g')"
		[ -z $index ] || pactl unload-module $index
}

remove (){
	vi=$1

	index="$(pacmd list-modules | grep -B 2 "$vi>" | grep index | sed 's/[^0-9]*//g')"
	[ -z $index ] || pactl unload-module $index
}

volume (){
	vi=$2
	[ -z $vi ] && exit
	pactl set-$1-volume $vi $3%
}

get (){
		eval "j="\$$2""
		[ "$1" = "vol" ] && [ -z $j ] && echo 0
		[ -z $j ] &&  return
		case $1 in
			"sink")
				aux=$(pacmd list-sinks | grep -A 50 $j | grep alsa.card.name | sed 's/.*= //g; s/"//g')
			;;
			"virtual_sink")
				aux=$(pacmd list-sinks | grep $j >/dev/null && echo $j)
			;;
			"src")
				aux=$(pacmd list-sources | grep -A 37 $j | grep alsa.card_name | sed 's/.*= //g; s/"//g')
			;;
			"virtual_src")
				aux=$(pacmd list-sources | grep $j >/dev/null && echo $j)
			;;
			"vol")
				aux=$(pactl list $3 | grep -A 7 $j | tr ' ' '\n' | grep -m1 '%' | tr -d '%')
				[ -z $aux ]
				echo $aux
				exit
			;;
		esac

		if [ -z "$aux" ]; then 
			[ -z $3 ] && eval "echo "\$$2""
		else
			echo $aux
		fi

}

case $1 in
	"init")
		init $2 $3
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
		get $2 $3 $4
	;;
	"*") echo "command not found";;
esac
