#!/bin/bash

echo "machine github.com" > ~/.netrc
echo "login $GH_USER" >> ~/.netrc
echo "password $GH_TOKEN" >> ~/.netrc

git config --global user.email $GH_EMAIL
git config --global user.name $GH_USER

