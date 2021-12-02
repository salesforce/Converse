#!/bin/bash

# get the current git branch
CUR=`git rev-parse --abbrev-ref HEAD`

# identify the files that differ from main branch
FILES=`git diff-tree -r --diff-filter=d --no-commit-id --name-only origin/main $CUR`

# apply flake8 to python files 
for f in ${FILES[@]}
do
   if [ ${f: -3} == ".py" ]
   then
       flake8 $f
   fi
done
