import os
from random import random
from flask import Flask, request, render_template, jsonify
from flask_pymongo import PyMongo

APP = Flask(__name__)


APP.config['MONGO_URI'] = "mongodb://%s:%s@%s.documents.azure.com:10250/mean" % (
    os.environ['DBNAME'], os.environ['DBPASS'], os.environ['DBNAME']
)

# initialize the database connection
# mongo = PyMongo(APP)
# Meh

@APP.route('/')
def hello_world():
    return 'Hello, World!'


@APP.route('/1')
def hello_params():
    try:
        mongo = PyMongo(APP)
        return "Success!"
    except Exception as ex:
        return ex.message



# @APP.route('/test')
# def test_endpoint():
#     test_db = mongo.db.test
#     output = []
#     for s in test_db.find():
#         output.append(s)
#
#     return jsonify({'result': output}), 200
#
#
# @APP.route('/test_add')
# def test_add_endpoint():
#     test_db = mongo.db.test
#     result = test_db.insert({"key": random(), "$currentDate": {"ts": True}})
#     return jsonify({'result': result}), 200 if result is not None else 500


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
