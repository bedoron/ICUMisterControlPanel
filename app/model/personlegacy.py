import base64
from abc import ABCMeta, abstractmethod

import cognitive_face as CF
from bson import ObjectId
from pymongo.database import Collection


class FileSupplier(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def read(self):
        pass


class PersonLegacy(FileSupplier):
    def __init__(self, collection, person_document):
        super(PersonLegacy, self).__init__()
        self._id = ObjectId(person_document['_id'])
        self._image = person_document['image']
        self._ts = self._id.generation_time

        self._person_document = person_document  # type: dict
        self._collection = collection  # type: Collection
        self._was_detected = False
        self._detected_ids = None

    @property
    def document(self):
        return self._person_document

    @property
    def id(self):
        return self._id

    @property
    def image(self):
        return base64.b64decode(self._image)

    def read(self):
        return base64.b64decode(self._image)

    def delete(self):
        return self._collection.delete_one({"_id": self._id})

    @property
    def detected_ids(self):
        if not self._detected_ids:
            self._detected_ids = [face['faceId'] for face in CF.face.detect(self)]
            self._was_detected = True

        return self._detected_ids

    @property
    def ts(self):
        return self._ts

    @property
    def persistent_face_id(self):
        if 'persistent_face_id' in self._person_document:
            return self._person_document['persistent_face_id']
        return None

    def get_group_person_id(self, group_name):
        return self._person_document.get(group_name, {}).get('person_id', None)

    def add_trained_details(self, person_id, persistent_face_id, trained_for):
        pg_training_details = {
            'status': trained_for,
            trained_for: {'person_id': person_id, 'persistent_face_id': persistent_face_id}
        }

        self._collection.update_one({'_id': self._id},
                                    {
                                        '$set': pg_training_details,
                                        '$push': {'person_groups': trained_for, 'person_ids': person_id}
                                    })

    def remove_all_trained_details(self):
        allowed_keys = ['_id', 'image', 'status']
        removal_query = dict()
        for key in self._person_document.keys():
            if key in allowed_keys:
                continue

            removal_query[key] = ''

        result = self._collection.update_one({'_id': self._id}, {'$unset': removal_query, '$set': {'status': 'new'}})
        success = result.modified_count == 1

        return success

    def remove_trained_details(self, person_group_name):
        update_query = {
            '$unset': {person_group_name: ""},
            '$pull': {'person_groups': person_group_name}
        }

        person_id = self._person_document.get(person_group_name, {}).get('person_id', None)
        if person_id:
            update_query['$pull']['person_ids'] = person_id

        query_result = self._collection.update_one({'_id': self._id, person_group_name: {'$exists': True}},
                                                   update_query)
        return query_result.modified_count == 1

    def is_trained_for_group(self, group_name):
        if 'person_groups' not in self._person_document:
            return False

        return group_name in self._person_document['person_groups']

    @staticmethod
    def fetch_by_person_id(face_collection, person_id):
        result = face_collection.find_one({'person_ids': person_id})
        if result is None:
            return None

        return PersonLegacy(face_collection, result)

    @staticmethod
    def fetch(face_collection, object_id):
        """
        @type face_collection: Collection
        @type object_id: str
        :rtype: Person
        """
        _id = ObjectId(object_id)

        result = face_collection.find_one({'_id': _id})
        if result is None:
            return None

        return PersonLegacy(face_collection, result)


if __name__ == "__main__":
    from app.utils import initialize_cf, get_db

    initialize_cf()
    db = get_db()
    collection = db.get_collection('new_faces')
    person = PersonLegacy.fetch(collection, '5b45d2af2c3fc24698f41c2f')

    if person.is_known:
        print "Person is KNOWN"

    if person.is_unknown:
        print "person is Unknown"
