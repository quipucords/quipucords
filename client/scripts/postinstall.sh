#!/bin/bash

mkdir -p public/assets/rcue
cp -R node_modules/rcue/dist/* public/assets/rcue

mkdir -p public/assets/images
cp -R src/styles/images/* public/assets/images
