from typing import Optional, Any

import pymongo.results
from flask import Flask, request, abort, send_from_directory, make_response, jsonify, g, current_app
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from pymongo import errors
from bson.objectid import ObjectId
import os

app = Flask(__name__)

app.config['FILEPATH'] = os.getenv('FILEPATH', '/document_storage')
app.config['DBHOST'] = os.getenv('DBHOST', 'localhost')
app.config['DBUSER'] = os.getenv('DBUSER', 'root')
app.config['DBPASS'] = os.getenv('DBPASS', 'password')
app.config['DB'] = os.getenv('DB', 'docservice')
app.config['COL'] = os.getenv('COL', 'documents')


def get_db() -> MongoClient:
    if 'db' not in g:
        try:
            g.db = MongoClient(host=current_app.config.get('DBHOST'), username=current_app.config.get('DBUSER'),
                               password=current_app.config.get('DBPASS'))
        except errors.ServerSelectionTimeoutError:
            print("MONGODB SERVER TIMED OUT")
    return g.db


def close_db(e=None) -> None:
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route("/doc/<id>", methods=['GET', 'DELETE'])
def doc(id: str):
    if len(id) != 24:
        abort(400)
    doc = find_document(id)
    if doc is None:
        abort(404)

    if request.method == 'GET':
        try:
            return send_from_directory(app.config.get('FILEPATH'), str(doc['_id']), as_attachment=True,
                                       download_name=doc['filename'])
        except FileNotFoundError:
            print("FILE NOT FOUND IN FILESYSTEM BUT EXISTS IN DATABASE")
            abort(404)

    elif request.method == 'DELETE':
        if doc is None:
            abort(404)
        deleted_doc = delete_document(id)
        try:
            os.remove(os.path.join(app.config.get('FILEPATH'), id))
        except FileNotFoundError:
            print("FILE NOT FOUND IN FILESYSTEM BUT EXISTS IN DATABASE")
        return "OK"


@app.route("/doc", methods=['GET', 'POST'])
def list_docs():
    if request.method == 'GET':
        docs = find_documents()
        return jsonify(docs)
    elif request.method == 'POST':
        if len(request.files) != 1:
            abort(400)
        for name, file in request.files.items():
            filename = secure_filename(file.filename)
            doc = insert_document(filename=filename)
            file.save(os.path.join(app.config.get('FILEPATH'), str(doc.inserted_id)))
            return {'id': str(doc.inserted_id), 'filename': filename}

    abort(405)


def find_documents() -> list:
    docs = []
    for doc in get_db()[app.config.get('DB')][app.config.get('COL')].find():
        docs.append({'id': str(doc['_id']), 'filename': doc['filename']})
    return docs


def find_document(id: str) -> Optional[Any]:
    doc = get_db()[app.config.get('DB')][app.config.get('COL')].find_one({'_id': ObjectId(id)})
    return doc


def delete_document(id: str) -> pymongo.results.DeleteResult:
    doc = get_db()[app.config.get('DB')][app.config.get('COL')].delete_one({'_id': ObjectId(id)})
    return doc


def insert_document(filename: str) -> pymongo.results.InsertOneResult:
    doc = get_db()[app.config.get('DB')][app.config.get('COL')].insert_one({'filename': filename})
    return doc


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 8080))
