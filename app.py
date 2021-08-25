from typing import Optional, Any

import bson
import pymongo.results
from flask import Flask, request, abort, send_from_directory, make_response, jsonify, g, current_app
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
import shutil
import yaml
import os

app = Flask(__name__)

FILES_DIR = 'doc_storage'
USERNAME = 'root'
PASSWORD = 'password'
DATABASE = 'docservice'
COLLECTION = 'documents'


def get_db() -> MongoClient:
    if 'db' not in g:
        g.db = MongoClient(username=USERNAME, password=PASSWORD)
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
            return send_from_directory(FILES_DIR, str(doc['_id']), as_attachment=True,
                                       attachment_filename=doc['filename'])
        except FileNotFoundError:
            print("FILE NOT FOUND IN FILESYSTEM BUT EXISTS IN DATABASE")
            abort(404)

    elif request.method == 'DELETE':
        if doc is None:
            abort(404)
        deleted_doc = delete_document(id)
        try:
            os.remove(os.path.join(FILES_DIR, id))
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
            file.save(os.path.join(FILES_DIR, str(doc.inserted_id)))
            return {'id': str(doc.inserted_id), 'filename': filename}

    abort(405)


def find_documents() -> list:
    docs = []
    for doc in get_db()[DATABASE][COLLECTION].find():
        docs.append({'id': str(doc['_id']), 'filename': doc['filename']})
    return docs


def find_document(id: str) -> Optional[Any]:
    doc = get_db()[DATABASE][COLLECTION].find_one({'_id': ObjectId(id)})
    return doc


def delete_document(id: str) -> pymongo.results.DeleteResult:
    doc = get_db()[DATABASE][COLLECTION].delete_one({'_id': ObjectId(id)})
    return doc


def insert_document(filename: str) -> pymongo.results.InsertOneResult:
    doc = get_db()[DATABASE][COLLECTION].insert_one({'filename': filename})
    return doc
