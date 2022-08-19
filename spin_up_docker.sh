#!/bin/bash

sudo docker kill /nginx-container

sudo docker rm /nginx-container

sudo docker build -t custom-nginx .

sudo docker run --network host --name nginx-container -d custom-nginx