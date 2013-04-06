#!/bin/sh
#Set Paths
PATH=$PATH:/bin:/usr/local/bin:/share/Apps/local/bin:/share/Apps/local/libexec/git-core:/nmt/apps/bin;export PATH
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/lib:opt/syb/app/lib:/nmt/app/lib:/opt/syb/sigma/lib:/usr/local/bin:/share/Apps/local/lib;export LD_LIBRARY_PATH
MANPATH=$MANPATH:/usr/local/share/man:/share/Apps/local/share/man;export MANPATH


force_pchtrakt()
{
   chmod 777 /share/Apps/pchtrakt
   cd /share/Apps/pchtrakt
   mkdir /share/tmp
   cd /share/tmp
   
   git clone git://github.com/cptjhmiller/pchtrakt.git pchtrakt
    
   cp -R pchtrakt/* /share/Apps/pchtrakt
   chmod -R 777 /share/Apps/pchtrakt
   cp -f /share/Apps/pchtrakt/scripts_install/update.py /share/Apps/pchtrakt/
   cp -f /share/Apps/pchtrakt/scripts_install/appinfo.json /share/Apps/pchtrakt/
   cp -f /share/Apps/pchtrakt/scripts_install/daemon.sh /share/Apps/pchtrakt/
   rm -fr /share/Apps/pchtrakt/scripts_install/
   cd
   rm -r /share/tmp
}

force_all()
{
    opkg update
    opkg install python2.7-dev -force-depends -force-overwrite
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
        kill -9 `pidof python2.7 pchtrakt.py` >/dev/null 2>/dev/null
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