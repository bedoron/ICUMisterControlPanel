from mongoengine import StringField, ListField
from mongoengine.document import Document


class Person(Document):
    person_id = StringField(max_length=50, required=False)
    person_group = StringField(max_length=100, required=False)
    trained_faces = ListField(StringField(max_length=70), required=False)

    name = StringField(max_length=50, requred=True)
