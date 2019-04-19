# MLB2019

Our goal is to create a pipeline for predicting MLB games, placing ficticious automatic bets on those games, creating a database to store all of this data, and a dashboard to display our results. 

Project Team:

* Rocky Chen
* Kasey Jones


## Requirements
This project relies on a docker container. Locally, this container makes sure all team members are using the same packages. At the server level, I am not sure what it will do yet. 

### Create the container

From the root directory of the project:

`docker-compose build`

### Open Container
`docker-compose run --rm mlb2019 bash`

## Starting a database
Sign-up for Amazon web serives and create a postgresql instance. I used the free tier. Amazon [RDS Free Tier](https://us-east-2.console.aws.amazon.com)

Download a way to communicate with the database: [pg admin 4](https://www.pgadmin.org/), although we will mostly use python to communicate. 

## Connect to the database:

Note that publicly available must be `yes`. Add security group to be custom TCP rule and select anywhere. 

hostname: `mlb2019.cvsp9ebtej6h.us-east-2.rds.amazonaws.com`

port: `5432`

username: `kaseyriver11`

## Loading Data in Postgres

[link](https://www.dataquest.io/blog/loading-data-into-postgres/)


