if [ -e ./core ]; then
	#Delete the core file if exists, sometimes the binary won't
	#delete it and then replace with a new core
	rm -f ./core
fi

VERSION=$(cat major-version.txt)

( sudo ./deb.py --default-version || \
(echo "You may need to run 'make deps' and/or ./ubuntu_deps.sh first"  \
&& false )) \
&& sudo dpkg -i ../ubuntu/$VERSION*.deb

