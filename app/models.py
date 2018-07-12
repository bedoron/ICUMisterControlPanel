import base64
from abc import ABCMeta, abstractmethod

from bson import ObjectId
from cognitive_face import CognitiveFaceException
from pymongo.database import Collection
import cognitive_face as CF

from utils import IGNORE_PERSON_GROUP, KNOWN_PERSON_GROUP, UNKNOWN_PERSON_GROUP


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

        self._person_document = person_document
        self._collection = collection  # type: Collection
        self._was_detected = False
        self._detected_ids = None

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
        if self._detected_ids is None:
            self._detected_ids = [face['faceId'] for face in cf.face.detect(person)]
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

    @property
    def person_id(self):
        if 'person_id' in self._person_document:
            return self._person_document['person_id']
        return None

    def add_trained_details(self, person_id, persistent_face_id, trained_for):
        self._collection.update_one({'_id': self._id},
                                    {'$set': {'person_id': person_id, 'persistent_face_id': persistent_face_id,
                                              'status': trained_for}})

    def is_trained_for_group(self, group_name):
        try:
            identified = cf.face.identify(self.detected_ids, group_name.lower())
            return identified is not None and len(identified) > 0
        except CognitiveFaceException as ex:
            if ex.status_code not in [404, 400]:
                raise ex

        return False

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


if __name__ == "__main__":
    from utils import initialize_cf, get_db
    import cognitive_face as cf

    initialize_cf()
    db = get_db()
    collection = db.get_collection('new_faces')
    person = Person.fetch(collection, '5b45d2af2c3fc24698f41c2f')

    if person.is_known:
        print "Person is KNOWN"

    if person.is_unknown:
        print "person is Unknown"
