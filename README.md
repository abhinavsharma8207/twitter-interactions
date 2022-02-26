# tora-twitter-interactions

* Embed in Flask API
* The Tora-Scheduler(Java Application Created for Running Schedulers) Executes scheduler after every configured Nth Interval to Get user profiles who Retweeted and Liked the tweet which  matches the tweet Ids which were fetched from the ToraApi and calls get_retweets_likes action method of tora-twitter-interactions to Get User Profiles Who liked or Retweeted. The user profiles are published to RABBITMQ Queue named interactions



## Prerequisite

```
The below mentioned docker application containers should be running before running the tora-twitter-interactions application container
```
* RabbitMQ docker container should be up and running. Please use the below mentioned configuration in the docker compose file to set up rabbitmq container 
  ```
  rabbitmq
    rabbitmq:
        image: 'rabbitmq:3-management'
        ports:
            - '5672:5672'
            - '15672:15672'
        restart: unless-stopped
        container_name: tora-rabbit
        volumes:
            - type: bind
              source: '/Users/data/dmi/rabbitmq' --- this path should be present on the local computer
              target: '/var/lib/rabbitmq'
  ```            
* Tora-Api container should be up and running - please refer the url for setting up tora-api container https://gitlab.g42.ae/pax-defence/DMI/tora-app/-/blob/development/README.md
* Tora-Scheduler container should be up and running - please refer the url for setting up tora-scheduler container https://gitlab.g42.ae/pax-defence/DMI/tora-scheduler/-/blob/development/README.md


## Build the docker image

```
docker build -t tora-twitter-interactions:latest .
```

## Save the image as fully contained

```
docker save -o tora-twitter-interactions.tar tora-twitter-interactions:latest
```

## Run the docker image

```
docker run -it -p 5000:5000 -e RABBITMQ_USER=guest -e RABBITMQ_PASSWORD=guest -e RABBITMQ_HOST=docker.for.mac.localhost -e ENABLE_CHROME_DRIVER=true -e --rm --name tora-twitter-interactions tora-twitter-interactions:latest
```
