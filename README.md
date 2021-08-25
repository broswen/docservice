# DocService
Simple document storage service written in [Python](https://www.python.org/) using the [Flask](https://flask.palletsprojects.com/en/2.0.x/) framework and [MongoDB](https://www.mongodb.com/).

1. `POST /doc` documents using form data, the service saves meta-data in MongoDB and stores the document at a predefined location.
2. `GET /doc` to get all documents and meta-data from MongoDB
3. `GET /doc/<id>` to download the file by id
4. `DELETE /doc/<id>` to delete the file by id


### Docker Compose
1. Run `docker-compose up` to start the service with a MongoDB instance.
2. Create the specified database and collection for the service to use in MongoDB.