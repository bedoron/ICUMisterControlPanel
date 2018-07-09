import os
import random
from ssl import CERT_NONE
import pymongo
from flask import Flask, request, render_template, jsonify

APP = Flask(__name__)

uri = "mongodb://%s:%s@%s.documents.azure.com:10255/?ssl=true&replicaSet=globaldb" % (
    os.environ['DBNAME'], os.environ['DBPASS'], os.environ['DBNAME'])

APP.config['MONGO_URI'] = uri

client = pymongo.MongoClient(uri, ssl_cert_reqs=CERT_NONE)
db = client.get_database('icumister')
test_collection = db.get_collection('test')


# initialize the database connection


@APP.route('/')
def hello_world():
    return "Hello dawgs!"


@APP.route('/test')
def test_endpoint():
    try:

        output = []
        for s in test_collection.find():
            output.append(s)

        return jsonify({'result': output}), 200
    except Exception as ex:
        return ex.message, 500


@APP.route('/test_add')
def test_add_endpoint():
    try:
        result = test_collection.insert_one(
            {"key": "bla_" + str(random.randint(10000, 99999)), "value": str(random.randint(10000, 99999))})

        return jsonify({'result': result}), 200 if result is not None else 500
    except Exception as ex:
        return ex.message, 500


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
