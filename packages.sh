#!/bin/sh

cd fedora
./copr_dl.py 
cd ..
cd ubuntu
./launchpad_dl.py 

