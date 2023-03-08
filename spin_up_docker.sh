#!/bin/bash

sudo docker kill /nginx-container

sudo docker rm /nginx-container

sudo docker build -t custom-nginx .

sudo docker run --network host \
  --name nginx-container \
  -e TZ=Europe/Berlin \
  -v $PWD/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /var/log/nginx:/var/log/nginx \
  -d custom-nginx