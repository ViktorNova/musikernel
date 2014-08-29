#Warning:  pre-alpha software

Backwards compatibility will be broken frequently and without warning or remorse until the project is declared to be in beta phase.  Expect bugs, and don't expect your projects to load next time you update your installation.

#What is MusiKernel ?

Without going into too much detail just yet, MusiKernel is DAWs, plugins, and a new approach to developing an audio software ecosystem.

#How to build:

#Ubuntu/Debian distros:

cd [musikernel src dir]/src

./ubuntu_deps.sh

make deps

make deb

cd ..

sudo dpkg -i musikernel[your_version].deb

#Fedora based distros:

cd [musikernel src dir]/src

./fedora_deps.sh

make rpm

cd ~/rpmbuild/RPMS/[your arch]

sudo yum localinstall musikernel[version number].rpm

#All others:

 # [figure out the dependencies based on the Fedora or Ubuntu dependencies]

cd [musikernel src dir]/src

make

 # You can specify DESTDIR or PREFIX if packaging, the result is fully relocatable

make install

