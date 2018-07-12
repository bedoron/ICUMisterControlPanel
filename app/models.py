import base64
from abc import ABCMeta, abstractmethod

from bson import ObjectId
from bson.errors import InvalidId
from cognitive_face import CognitiveFaceException
from pymongo.database import Collection
import cognitive_face as CF

from app.utils import IGNORE_PERSON_GROUP, KNOWN_PERSON_GROUP, UNKNOWN_PERSON_GROUP


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

    def delete(self):
        return self._collection.delete_one({"_id": self._id})

    @property
    def ts(self):
        return self._ts

    def add_trained_details(self, person_id, persistent_face_id, trained_for):
        self._collection.update_one({'_id': self._id},
                                    {'$set': {'person_id': person_id, 'persisten_face_id': persistent_face_id,
                                              'status': trained_for}})

    def is_trained_for_group(self, group_name):
        try:
            cf_person = CF.person.get(group_name.lower(), self._id)
        except CognitiveFaceException as ex:
            if ex.status_code != 404:
                raise ex
            else:
                return False

        return cf_person is not None

    @property
    def is_known(self):
        return self.is_trained_for_group(KNOWN_PERSON_GROUP)

    @property
    def is_unknown(self):
        return self.is_trained_for_group(UNKNOWN_PERSON_GROUP)

    @property
    def is_ignored(self):
        return self.is_trained_for_group(IGNORE_PERSON_GROUP)

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
