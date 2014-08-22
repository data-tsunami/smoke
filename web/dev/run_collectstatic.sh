#!/bin/bash

cd $(dirname $0; pwd)
cd ..
cd ..

python manage.py collectstatic  --noinput --no-post-process

while /bin/true ; do
	sleep 3600
done

