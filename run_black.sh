#!/bin/bash

pip install -U black==20.8b1

# get the current git branch
CUR=`git rev-parse --abbrev-ref HEAD`

# identify the files that differ from main branch
FILES=`git diff-tree -r --diff-filter=d --no-commit-id --name-only origin/main $CUR`

# apply black to python files
for f in ${FILES[@]}
do
   if [ ${f: -3} == ".py" ]
   then
       # The "--fast" flag is added to work around this Black Github issue:
       # https://github.com/psf/black/issues/1629
       black --fast $f
   fi
done
