#!/bin/sh
#Set Paths
PATH=$PATH:/bin:/usr/local/bin:/share/Apps/local/bin:/share/Apps/local/libexec/git-core:/nmt/apps/bin;export PATH
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/lib:opt/syb/app/lib:/nmt/app/lib:/opt/syb/sigma/lib:/usr/local/bin:/share/Apps/local/lib;export LD_LIBRARY_PATH
MANPATH=$MANPATH:/usr/local/share/man:/share/Apps/local/share/man;export MANPATH


force_pchtrakt()
{
   # install coreutils
	if [ -f /share/Apps/local/bin/tr ] ; then
		echo "Required dependency, coreutils is installed."
	else
		opkg install coreutils -force-depends -force-overwrite
	fi
	chmod 777 /share/Apps/pchtrakt
	cd /share/Apps/pchtrakt
	git stash
	git pull
    sleep 5
	git reset
}

force_all()
{
    opkg update
    opkg install python2.7 -force-depends -force-overwrite
    opkg install git -force-depends -force-overwrite
    cd /share/Apps/pchtrakt/
}

start_pchtrakt()
{
    # start pchtrakt
    ps | grep "[p]chtrakt.py --daemon" > /dev/null
    if [ $? -ne 0 ];
    then
        echo "pchtrakt.py is not running, Starting processes"
        cd /share/Apps/pchtrakt
        python2.7 pchtrakt.py --daemon
        cd
    fi
}

stop_pchtrakt()
{
# Stop pchtrakt
if [ -n "`ps | grep "pchtrakt" | grep -v "grep"`" ]; then
        kill -9 `ps -A |grep pchtrakt.py | grep -v grep |head -n 1 | awk '{print $1}'` >/dev/null 2>/dev/null
        sleep 2
fi
}

#Main
case "$1" in
    start)
    start_pchtrakt;
    ;;

    stop)
    stop_pchtrakt;
    exit
    ;;

    restart)
    stop_pchtrakt;
    sleep 2
    start_pchtrakt;
    ;;

    update)
    stop_pchtrakt;
    sleep 2
    force_pchtrakt;
    sleep 2
    start_pchtrakt;
    ;;
    
    forceall)
    stop_pchtrakt;
    sleep 2
        force_all;
    force_pchtrakt;
    sleep 2
        start_pchtrakt;
    ;;
esac