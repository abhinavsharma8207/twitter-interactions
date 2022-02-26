#!/bin/sh

docker build -t tora-twitter-interactions  -f tests/Dockerfile .
docker pull docker.g42.ae/docker-dmi/docker-hub/rabbitmq:3-management

if [ $? -ne 0 ]
then
    echo "ERROR ---> There is an error in building the image"
    exit 1
fi

echo "Test cases starting ...."
docker run --rm -tt \
            --privileged \
            --shm-size=512m \
            -v $(pwd):/data \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v /dev/shm:/dev/shm \
            -e TZ=UTC \
            --network host \
            --entrypoint "/bin/bash" \
              tora-twitter-interactions -c "bash tests/gitlab_running.sh;" \

if [ $? -ne 0 ]
then
    echo "ERROR ---> There is an error in building the image"
    exit 1
fi