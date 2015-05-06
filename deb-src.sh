git pull
MAJOR_VERSION=$(cat src/major-version.txt)
MINOR_VERSION=$(cat src/minor-version.txt)
FULL_VERSION=$(MAJOR_VERSION)-$(MINOR_VERSION)
CHANGES_FILE=$(MAJOR_VERSION)_$(MINOR_VERSION)-1_source.changes

cp -r src $FULL_VERSION
cd $FULL_VERSION
debuild -S -sa -k412C4B95
cd ..
dput ppa:musikernel/musikernel $(CHANGES_FILE)

