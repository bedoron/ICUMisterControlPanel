import base64
import json
import os
import time

from bson import ObjectId
from cognitive_face import CognitiveFaceException
from flask import Flask
from flask import render_template, jsonify, request, flash, redirect, Response, url_for
from flask_mongo_sessions import MongoDBSessionInterface
from flask_mongoengine.wtf import model_form
from pymongo.database import Database
from werkzeug.datastructures import FileStorage
from flask_mongoengine import MongoEngine

from model.person import Person
from model.notification import Notification
from model.face import Face
from model.personlegacy import PersonLegacy
from person_group import PersonGroup
from utils import get_db, JSONEncoder, initialize_cf, IGNORE_PERSON_GROUP, UNKNOWN_PERSON_GROUP, KNOWN_PERSON_GROUP, \
    setup_mongoengine
from forms import FaceUploadForm, PersonCreateForm

APP = Flask(__name__)

# This is for XHR
APP.config['SECRET_KEY'] = os.environ['AZURE_CLIENT_SECRET']
APP.config['WTF_CSRF_ENABLED'] = False

setup_mongoengine(APP)
MongoEngine(APP)

db = get_db()  # type: Database
APP.session_interface = MongoDBSessionInterface(APP, db, 'sessions')  # Setup session handler using mongo

# TODO: Deprecated
test_collection = db.get_collection('test')
# TODO: Deprecated
new_faces = db.get_collection('new_faces')

face_collection = db.get_collection('faces')  # Images dump
persons_collection = db.get_collection('persons')  # Only known people

# Initialize Cognitive face
try:
    initialize_cf()
except Exception as ex:
    flash('Failed to initialize CF: {}'.format(ex), category='danger')

# use the modified encoder class to handle ObjectId & datetime object while jsonifying the response.
APP.json_encoder = JSONEncoder


@APP.errorhandler(Exception)
def exception_handler(ex):
    return jsonify({'error': ex.message}), 500


@APP.route('/')
def show_all():
    pending_users = []
    for new_face in new_faces.find():
        object_id = ObjectId(new_face['_id'])
        img_url = url_for('get_face_image', object_id=object_id)

        train_known_face = url_for('train_face_known', object_id=object_id)
        train_ignore_face = url_for('train_face_ignore', object_id=object_id)
        delete_face_url = url_for('delete_face', object_id=object_id)
        person_info_url = url_for('person_info', object_id=object_id)

        status = 'untrained' if new_face['status'] == 'new' else new_face['status']

        pending_users.append(
            {'ts': object_id.generation_time, 'id': object_id, 'img_url': img_url, 'train_known': train_known_face,
             'train_ignore': train_ignore_face, 'delete_face_url': delete_face_url, 'info_url': person_info_url,
             'status': status})

    return render_template('pending_users.html', pending_users=pending_users)


@APP.route('/person/json/<object_id>')
def person_info(object_id):
    person = PersonLegacy.fetch(new_faces, object_id)
    return jsonify(person.document)


@APP.route('/person/identify/<object_id>')
def person_identify(object_id):
    person = PersonLegacy.fetch(new_faces, object_id)
    possible_matches = []
    for pg in [PersonGroup.known_person_group(), PersonGroup.unknown_person_group(), PersonGroup.ignore_person_group()]:
        identification_result = pg.identify(person)
        if not identification_result:
            continue

        for candidates in identification_result.values():
            for candidate in candidates:
                person_id = candidate['personId']
                matching_person = PersonLegacy.fetch_by_person_id(new_faces, person_id)
                if not matching_person:
                    continue

                possible_matches.append(matching_person.id)

        time.sleep(1)

    if person.id not in possible_matches:
        possible_matches.append(person.id)
    return jsonify(result=possible_matches), 200


@APP.route('/reset_training')
def reset_training():
    PersonGroup.reset_all()
    for face_document in new_faces.find():
        person = PersonLegacy(new_faces, face_document)
        person.remove_all_trained_details()

    flash('Reset all training group', category='info')
    return redirect('/')


@APP.route('/face/known/<object_id>')
def is_face_known(object_id):
    person = PersonLegacy.fetch(new_faces, object_id)

    person_group_id = person.get_group_person_id(KNOWN_PERSON_GROUP)
    result = person_group_id is not None

    if not result:
        result = person in PersonGroup.known_person_group()

    return jsonify({'result': result})


@APP.route('/face/unknown/<object_id>')
def is_face_unknown(object_id):
    person = PersonLegacy.fetch(new_faces, object_id)
    return jsonify({'result': person.get_group_person_id(UNKNOWN_PERSON_GROUP)})


@APP.route('/face/ignored/<object_id>')
def is_face_ignored(object_id):
    person = PersonLegacy.fetch(new_faces, object_id)
    return jsonify({'result': person.get_group_person_id(IGNORE_PERSON_GROUP)})


@APP.route('/face/image/<object_id>')
def get_face_image(object_id):
    person = PersonLegacy.fetch(new_faces, object_id)
    return Response(person.image, mimetype='image/jpeg')


@APP.route('/person/delete/<object_id>')
def delete_face(object_id):  # TODO: Sanitize this input
    person = PersonLegacy.fetch(new_faces, object_id)
    result = person.delete()
    if result is None:
        flash('Failed deleting: {}'.format(json.dumps(result)))

    return redirect('/')


@APP.route('/train_face/ignore/<object_id>')
def train_face_ignore(object_id):
    person_group = PersonGroup.ignore_person_group()
    return train_face(object_id, person_group)


@APP.route('/train_face/known/<object_id>')
def train_face_known(object_id):
    person_group = PersonGroup.known_person_group()
    return train_face(object_id, person_group)


@APP.route('/train_face/unknown/<object_id>')
def train_face_unknown(object_id):
    person_group = PersonGroup.unknown_person_group()
    return train_face(object_id, person_group)


def train_face(object_id, person_group):
    person = PersonLegacy.fetch(new_faces, object_id)
    try:
        person_group.add_person(person)
    except CognitiveFaceException as ex:
        if ex.status_code in [400, 404]:
            flash("Face not detected, can't add to group - " + person_group.name, category='warning')
            return redirect('/')
    except Exception as ex:
        flash("API Failed - {}".format(ex.message), category="danger")
        return redirect("/")

    unknown_person_group = PersonGroup.unknown_person_group()
    if not unknown_person_group.remove_person(person):
        flash("Face doesn't exist in " + unknown_person_group.name + " so it wasn't removed", category='info')
    return redirect("/")


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
        flash('No file selected', category='danger')
        return render_template('add_face.html')

    with file.stream as f:
        b64_file = base64.b64encode(f.read())

    if b64_file is None:
        flash('Failed converting file to b64')
        return render_template('add_face.html')

    try:
        result = new_faces.insert({'image': b64_file, 'status': 'new'})
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


@APP.route('/face/create', methods=['POST', 'GET'])
def face_store():
    fuf = FaceUploadForm()
    if fuf.is_submitted():
        face = Face.create(face_collection, fuf.file.data.read())
        flash('Added face id ' + str(face.id), category='info')
        return redirect('/')

    return render_template('face_add_form.html', form=fuf)


@APP.route('/face/<object_id>')
def face_get(object_id):
    face = Face.find(face_collection, ObjectId(object_id))
    if not face:
        return "Error", 500

    return Response(face.image, mimetype='image/jpeg')


@APP.route('/face/delete/<object_id>')
def face_delete(object_id):
    Face.delete(face_collection, ObjectId(object_id))
    flash('Deleted face ' + str(object_id))
    return redirect(url_for('show_all_faces'))


@APP.route('/face/update/<object_id>')
def face_update(object_id):
    pass  # http://wtforms.simplecodes.com/docs/0.6.1/fields.html (look at "Select fields with dynamic choice value")


@APP.route('/face')
def show_all_faces():
    faces = Face.find_all(face_collection)
    return render_template('show_all_faces.html', faces=faces)


@APP.route('/person')
def show_all_people():
    people = Person.f
    pass


@APP.route('/person/<object_id>')
def get_person(object_id):
    pass


@APP.route('/person/create', methods=['GET', 'POST'])
def create_person():
    PersonForm = model_form(Person)

    form = PersonForm()
    if request.method == 'POST' and form.validate():
        form.save(validate=False)
        flash('Person {} successfully save'.format(form.name), category='danger')

    return render_template('person_form.html', form=form)


@APP.route('/person/update/<object_id>')
def update_person(object_id):
    pass


@APP.route('/person/delete/<object_id>')
def delete_person(object_id):
    pass


@APP.route('/notifications/<notification_id>')
def show_notification(notification_id):  # Show in mobile page
    pass


@APP.route('/notifications/<notification_id>/dismiss', methods=['POST'])
def dismiss(notification_id):
    pass


@APP.route('/notifications/<notification_id>/add', methods=['POST'])
def new_person_from_notification(notification_id):  # Create a new person from notification image
    pass


# Dummy method to create notification online
@APP.route('/notifications/create', methods=['GET', 'POST'])
def create_notification():  # Create a new person from notification image
    NotificationForm = model_form(Notification, field_args={'msg': {'textarea': True}})

    form = NotificationForm(request.form)
    if request.method == 'POST' and form.validate():
        form.save(validate=False)
        flash('success!', category='success')

    return render_template('add_notification.html', form=form)


@APP.route('/notifications/')
def show_all_notifications():
    all_notifications = Notification.objects()
    return render_template('show_all_notifications.html', notifications=all_notifications)


if __name__ == '__main__':
    APP.run()
