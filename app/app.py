import base64
import json

import cognitive_face as CF
from bson import ObjectId
from cognitive_face import CognitiveFaceException
from flask import Flask
from flask import render_template, jsonify, request, flash, redirect, Response, url_for
from flask_mongo_sessions import MongoDBSessionInterface
from pymongo.database import Database
from werkzeug.datastructures import FileStorage

from models import Person
from utils import get_db, JSONEncoder, get_secret, initialize_cf, KNOWN_PERSON_GROUP, \
    UNKNOWN_PERSON_GROUP, IGNORE_PERSON_GROUP

APP = Flask(__name__)

db = get_db()  # type: Database
APP.session_interface = MongoDBSessionInterface(APP, db, 'sessions')

test_collection = db.get_collection('test')
new_faces = db.get_collection('new_faces')

# Initialize Cognitive face
try:
    initialize_cf()
except Exception as ex:
    flash('Failed to initialize CF: {}'.format(ex), category='error')

# use the modified encoder class to handle ObjectId & datetime object while jsonifying the response.
APP.json_encoder = JSONEncoder


@APP.errorhandler(Exception)
def expection_handler(ex):
    return jsonify(ex), 500


@APP.route('/')
def show_all():
    pending_users = []
    for new_face in new_faces.find():
        object_id = ObjectId(new_face['_id'])
        img_url = url_for('get_face_image', object_id=object_id)

        train_known_face = url_for('train_face_known', object_id=object_id)
        train_ignore_face = url_for('train_face_ignore', object_id=object_id)
        delete_face_url = url_for('delete_face', object_id=object_id)
        status = 'untrained' if new_face['status'] == 'new' else new_face['status']

        pending_users.append(
            {'ts': object_id.generation_time, 'id': object_id, 'img_url': img_url, 'train_known': train_known_face,
             'train_ignore': train_ignore_face, 'delete_face_url': delete_face_url, 'status': status})

    return render_template('pending_users.html', pending_users=pending_users)


@APP.route('/face/known/<object_id>')
def is_face_known(object_id):
    person = Person.fetch(new_faces, object_id)
    return jsonify({'result': person.is_known})


@APP.route('/face/unknown/<object_id>')
def is_face_unknown(object_id):
    person = Person.fetch(new_faces, object_id)
    return jsonify({'result': person.is_unknown})


@APP.route('/face/ignored/<object_id>')
def is_face_ignored(object_id):
    person = Person.fetch(new_faces, object_id)
    return jsonify({'result': person.is_ignored})


@APP.route('/face/image/<object_id>')
def get_face_image(object_id):
    person = Person.fetch(new_faces, object_id)
    return Response(person.image, mimetype='image/jpeg')


@APP.route('/face/delete/<object_id>')
def delete_face(object_id):  # TODO: Sanitize this input
    person = Person.fetch(new_faces, object_id)
    result = person.delete()
    if result is None:
        flash('Failed deleting: {}'.format(json.dumps(result)))

    return redirect('/')


@APP.route('/train_face/ignore/<object_id>')
def train_face_ignore(object_id):
    api_key = get_secret('faceKey1')  # type: str
    return 'Training face ' + object_id + ' as ignore'


@APP.route('/train_face/known/<object_id>')
def train_face_known(object_id):
    person = Person.fetch(new_faces, object_id)

    if person.is_trained_for_group(KNOWN_PERSON_GROUP):
        flash("Person already exists in group {}".format(KNOWN_PERSON_GROUP), category='warning')
        return redirect("/")

    person_result = CF.person.create(KNOWN_PERSON_GROUP.lower(), object_id)
    person_id = person_result['personId']
    try:
        persistent_face_id = CF.person.add_face(person, KNOWN_PERSON_GROUP.lower(), person_id)
        CF.person_group.train(KNOWN_PERSON_GROUP.lower())
        person.add_trained_details(person_id, persistent_face_id, KNOWN_PERSON_GROUP)
    except CognitiveFaceException as e:
        if e.status_code == 400:
            flash("No face in image")
            return redirect('/')

    # Now lets remove this face from unknown person group because we know him now
    if not person.is_trained_for_group(UNKNOWN_PERSON_GROUP):
        flash("Person didn't exist in unknown group")
        return redirect("/")

    flash("Bleh")
    return redirect("/")


@APP.route('/train_face/unknown/<object_id>')
def train_face_unknown(object_id):
    return 'Training face ' + object_id + ' as unknown'


@APP.route('/test')
def test_endpoint():
    try:
        output = []
        for s in new_faces.find():
            output.append(ObjectId(s['_id']))

        return jsonify({'result': output}), 200
    except Exception as ex:
        return ex.message, 500


def _store_uploaded_face():
    if 'faceImage' not in request.files:
        flash('No file uploaded')
        return render_template('add_face.html')

    file = request.files['faceImage']  # type: FileStorage
    if file.filename == '':
        flash('No file selected')
        return render_template('add_face.html')

    with file.stream as f:
        b64_file = base64.b64encode(f.read())

    if b64_file is None:
        flash('Failed converting file to b64')
        return render_template('add_face.html')

    try:
        result = new_faces.insert({'image': b64_file, "status": "new"})
    except Exception as ex:
        flash(ex.message)
        return render_template('add_face.html')

    return redirect('/')


@APP.route('/add_face', methods=['GET', 'POST'])
def add_face():
    if request.method == 'POST':
        return _store_uploaded_face()
    else:
        return render_template('add_face.html')


if __name__ == '__main__':
    APP.run()
