import base64
from abc import ABCMeta, abstractmethod

from bson import ObjectId
from cognitive_face import CognitiveFaceException
from pymongo.database import Collection
import cognitive_face as CF


class FileSupplier(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def read(self):
        pass


class Person(FileSupplier):
    def __init__(self, collection, person_document):
        super(Person, self).__init__()
        self._id = ObjectId(person_document['_id'])
        self._image = person_document['image']
        self._ts = self._id.generation_time

        self._collection = collection  # type: Collection

    @property
    def id(self):
        return self._id

    @property
    def image(self):
        return base64.b64decode(self._image)

    def read(self):
        return base64.b64decode(self._image)

    @property
    def ts(self):
        return self._ts

    def add_trained_details(self, person_id, persistent_face_id):
        self._collection.update_one({'_id': self._id},
                                    {'$set': {'person_id': person_id, 'persisten_face_id': persistent_face_id}})

    def is_trained_for_group(self, group_name):
        try:
            cf_person = CF.person.get(group_name.lower(), self._id)
        except CognitiveFaceException as ex:
            if ex.status_code != 404:
                raise ex
            else:
                return False

        return cf_person is not None

    @staticmethod
    def fetch(collection, object_id):
        """
        @type collection: Collection
        @type object_id: str
        :rtype: Person
        """
        _id = ObjectId(object_id)
        result = collection.find_one({'_id': _id})
        if result is None:
            return None

        return Person(collection, result)
