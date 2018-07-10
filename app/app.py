import base64
import random

from bson import ObjectId
from flask import Flask, render_template, jsonify, request, flash, redirect, Response, url_for
from pymongo.database import Database
from werkzeug.datastructures import FileStorage

from utils import get_key_vault, get_db, JSONEncoder

APP = Flask(__name__)


db = get_db()  # type: Database
test_collection = db.get_collection('test')
new_faces = db.get_collection('new_faces')

keyvault = get_key_vault()

# use the modified encoder class to handle ObjectId & datetime object while jsonifying the response.
APP.json_encoder = JSONEncoder


@APP.route('/')
def hello_world():
    pending_users = []
    for new_face in new_faces.find({"status": "new"}):
        img_url = url_for('get_face_image', object_id=new_face['_id'])
        pending_users.append({'ts': new_face["ts"], 'id': new_face['_id'], 'img_url': img_url})

    return render_template('pending_users.html', pending_users=pending_users)


@APP.route('/face/image/<object_id>')
def get_face_image(object_id):  # TODO: Sanitize this input
    if object_id is None:
        return "Error", 404
    object_id = ObjectId(object_id)

    face = new_faces.find_one({'_id': object_id})
    if face is None:
        return "Not found", 404

    face_image = base64.b64decode(face['image'])
    return Response(face_image, mimetype='image/jpeg')


@APP.route('/train_face/known/<object_id>')
def train_face_known(object_id):
    return 'Training face ' + object_id + ' as known'


@APP.route('/train_face/unknown/<object_id>')
def train_face_unknown(object_id):
    return 'Training face ' + object_id + ' as unknown'


@APP.route('/test')
def test_endpoint():
    try:

        output = []
        for s in test_collection.find():
            output.append(s)

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

    b64_file = None
    with file.stream as f:
        b64_file = base64.b64encode(f.read())

    if b64_file is None:
        flash('Failed converting file to b64')
        return render_template('add_face.html')

    try:
        result = new_faces.update_one({}, {"$set": {'image': b64_file, "status": "new"}, "$currentDate": {"ts": True}},
                                      upsert=True)
    except Exception as ex:
        flash(ex.message)
        return render_template('add_face.html')

    return redirect('/')

    # try:
    #     # Base64 face data and store it in the DB
    #     result = test_collection.insert_one(
    #         {"key": "bla_" + str(random.randint(10000, 99999)), "value": str(random.randint(10000, 99999))})
    #
    #     return jsonify({'result': result}), 200 if result is not None else 500
    # except Exception as ex:
    #     return ex.message, 500


@APP.route('/add_face', methods=['GET', 'POST'])
def add_face():
    if request.method == 'POST':
        return _store_uploaded_face()
    else:
        return render_template('add_face.html')


#
#
# @APP.route('/')
# def view_registered_guests():
#     guests = Guest.query.all()
#     return render_template('guest_list.html', guests=guests)
#
#
# @APP.route('/register', methods = ['GET'])
# def view_registration_form():
#     return render_template('guest_registration.html')
#
#
# @APP.route('/register', methods = ['POST'])
# def register_guest():
#     name = request.form.get('name')
#     email = request.form.get('email')
#     partysize = request.form.get('partysize')
#     if not partysize or partysize=='':
#         partysize = 1
#
#     guest = Guest(name, email, partysize)
#     DB.session.add(guest)
#     DB.session.commit()
#
#     return render_template('guest_confirmation.html',
#         name=name, email=email, partysize=partysize)

if __name__ == '__main__':
    APP.run()
