#!/bin/sh
#Set Paths
PATH=$PATH:/bin:/usr/local/bin:/share/Apps/local/bin:/share/Apps/local/libexec/git-core:/nmt/apps/bin;export PATH
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/lib:opt/syb/app/lib:/nmt/app/lib:/opt/syb/sigma/lib:/usr/local/bin:/share/Apps/local/lib;export LD_LIBRARY_PATH
MANPATH=$MANPATH:/usr/local/share/man:/share/Apps/local/share/man;export MANPATH

configid=$(genxenv2 l /tmp/lrro.xenv 2>/dev/null | grep -e " lrro.configid" | sed -e's/.*lrro.configid\s*//' | sed 's/\ //g'| sed 's/0x//g')
configid="${configid[@]:0:4}"
install()
{
# Check opkg installation
if [ -d /share/Apps/local ]; then
	echo "Required dependency, opkg (local) is installed."
else
	echo "Required dependency, opkg (local) is not installed, Forcing install"
	mkdir /share/tmp
	cd /share/tmp
	if [ -e "/nmt/apps" ]; then
		if [ "$configid" = "8911" ]; then
			echo "Popcorn Hour A-400"
			wget http://freefr.dl.sourceforge.net/project/nmtcsi/opkg_a400_v0.1.8-nmt2.zip
			unzip opkg_a400_v0.1.8-nmt2.zip
		else
			echo "Popcorn Hour 200/300 series"
			wget http://freefr.dl.sourceforge.net/project/nmtcsi/opkg_c200_v0.1.8-nmt3.zip
			unzip opkg_c200_v0.1.8-nmt3.zip
		fi
	else
		echo "Popcorn Hour A-1xx/B-110"
		wget http://freefr.dl.sourceforge.net/project/nmtcsi/opkg_a110_v0.1.8-nmt1.zip
		unzip opkg_a110_v0.1.8-nmt1.zip
	fi
	mkdir /share/Apps/local
	chmod -R 777 /share/Apps/local
	tar xvf opkg.tar -C /share/Apps/local
	cd /
	/share/Apps/AppInit/appinit.cgi start local >/dev/null
	rm -r /share/tmp
fi
 
# Update opkg installation
opkg update

# install python2.7-dev
if [ -f /share/Apps/local/bin/python2.7 ]; then
	echo "Required dependency, python is installed."
else
	echo "Installing dependency, python2.7"
	chmod 777 /share/Apps/sickbeard
	if [ -e "/nmt/apps" ]; then
		opkg install python2.7 --force-depends --force-overwrite #--force-reinstall
		cd /share/Apps/sickbeard
		wget http://jamied.pwp.blueyonder.co.uk/donotdelete.tar.gz
		if [ "$configid" = "8911" ]; then
			tar zxf donotdelete.tar.gz -C /share/Apps/local/
		else
			tar zxf donotdelete.tar.gz -C /share/Apps/local/ ./lib
		fi
	else
		 #install g++-4.4
		if [ -f /share/Apps/local/bin/g++ ]; then
			echo "Required dependency, g++-4.4 is installed."
		else
			echo "Installing dependency, g++."
			opkg install g++-4.4 -force-depends -force-overwrite
		fi
		#install gcc-4.4
		if [ -f /share/Apps/local/bin/gcc ]; then
			echo "Required dependency, gcc-4.4 is installed."
		else
			echo "Installing dependency, gcc."
			opkg install gcc-4.4 -force-depends -force-overwrite
		fi
		#install Cheetah
		if [ -d /share/Apps/local/lib/python2.7/site-packages/Cheetah ] ; then     
			echo "Cheetah is installed"
		else
			cd /share/Apps/sickbeard/
			wget http://pypi.python.org/packages/source/C/Cheetah/Cheetah-2.4.4.tar.gz
			tar -zxvf Cheetah-2.4.4.tar.gz
			cd Cheetah-2.4.4
			/share/Apps/local/bin/python2.7 setup.py install
		 fi
		 #check hosts
		 name1=$(cat /etc/hostname)
		 if grep -q "$name1" /etc/hosts
		 then
			echo "Host name has been added already"
		 else
			echo "Host name added to list"
			echo "127.0.0.1 localhost localhost.images localhost.drives $name1" >/share/Apps/sickbeard/hosts
			cp /share/Apps/sickbeard/hosts /etc/hosts
		 fi
	fi
fi

# install git
if [ -f "/share/Apps/local/bin/git" ] ; then
	echo "Required dependency, git is installed."
else
	echo "Installing dependency, git."
	opkg install git -force-depends -force-overwrite
fi

# install expat
if [ -f /share/Apps/local/lib/python2.7/xml/parsers/expat.py ] ; then
	echo "Required dependency, expat is installed."
else
	echo "Installing dependency, expat."
	opkg install expat -force-depends -force-overwrite
fi

# install pchtrakt
if [ -d /share/Apps/pchtrakt/lib ] ; then 
	echo "pchtrakt is installed"
else
   chmod 777 /share/Apps/pchtrakt
   cd /share/Apps/pchtrakt
   mkdir /share/tmp
   cd /share/tmp
   
    if [ -f /share/Apps/pchtrakt/TEST ]; then
        git clone -b testing git://github.com/pchtrakt/pchtrakt.git pchtrakt
        else 
        git clone git://github.com/pchtrakt/pchtrakt.git pchtrakt
    fi  
 
   cp -R pchtrakt/* /share/Apps/pchtrakt
   chmod -R 777 /share/Apps/pchtrakt
   cp -f /share/Apps/pchtrakt/scripts_install/update.py /share/Apps/pchtrakt/
   cp -f /share/Apps/pchtrakt/scripts_install/appinfo.json /share/Apps/pchtrakt/
#   cp -f /share/Apps/pchtrakt/scripts_install/daemon.sh /share/Apps/pchtrakt/
   rm -fr /share/Apps/pchtrakt/scripts_install/
   cd
   rm -r /share/tmp
fi
}

uninstall()
{
    if [ -d /share/Apps/pchtrakt ]; then
		rm -R /share/Apps/pchtrakt
    fi
}


case "$1" in
    install)
    install
    ;;
    
    uninstall)
    uninstall
    ;;
esac