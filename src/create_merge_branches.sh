#!bin/sh

set -uex

tag=$1
branch="merge-libdparse-$tag"
dir=`mktemp -d`

echo "tag = $tag"
echo "branch = $branch"

function createMergeBranch()
{
    local repo=$1

    git clone "https://github.com/$GH_USER/$repo"

    cd $repo

    # add target url and fetch its master branch
    git remote add target "https://github.com/$GH_TARGET_USER/$repo"
    git fetch target master

    # create the merge branch from target/master and checkout libdparse
    git checkout target/master -b $branch
    git submodule update --init libdparse

    # change libdparse to point to thr new tag version
    cd libdparse
    git checkout "tags/$tag"
    cd ..

    # replace libdparse version requirement in dub.json
    sed -i -E "s/\"libdparse\": \"[^\"]*\"/\"libdparse\": \"~>${tag:1}\"/" dub.json

    # add the changes to the commit
    git add dub.json
    git add libdparse

    # create the commit and push it to remote
    git commit -m "Updated libdparse to $tag."
    git push -u origin $branch
}

for repo in DCD D-Scanner dfmt; do
    cd $dir
    createMergeBranch $repo
done

rm -rf $dir




