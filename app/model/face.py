import base64

from pymongo.collection import Collection, ObjectId


class Face(object):
    """
    Face document should look as following:
    {
        "_id": <mongo object id>
        "image": binary file data
    }
    """

    def __init__(self, id, encoded_image, person=None):
        super(Face, self).__init__()
        self._id = id
        self._image = base64.b64decode(encoded_image)
        self.person = person

    def read(self):
        return self._image

    def save(self, faces_collection):
        """
        :type faces_collection: Collection
        """
        to_db = {
            'image': base64.b64encode(self._image)
        }

        if self.person:
            to_db['person'] = self.person

        if self._id:
            faces_collection.update_one({'_id': self._id}, {'$set': to_db})
        else:
            result = faces_collection.insert_one(to_db)
            self._id = result.inserted_id

        return self._id

    @property
    def image(self):
        return self._image

    @property
    def id(self):
        """
        :rtype: ObjectId
        """
        return self._id

    @staticmethod
    def create(face_collection, binary_image, store=True):
        """
        :type face_collection: Collection
        :type binary_image: bytearray
        :type store: bool
        :rtype: Face
        """
        encoded_file = base64.b64encode(binary_image)
        if store:
            result = face_collection.insert_one({'image': encoded_file})
            return Face(result.inserted_id, encoded_file)
        else:
            return Face(None, encoded_file)

    @staticmethod
    def find(face_collection, object_id):
        """
        :type face_collection: Collection
        :type object_id: ObjectId
        :rtype: Face
        """
        face_document = face_collection.find_one({'_id': object_id})
        return Face(face_document['_id'], face_document['image'],
                    face_document.get('person', None)) if face_document else None

    @staticmethod
    def find_all(face_collection, query=None):
        """
        :type face_collection: Collection
        :type query: dict
        :rtype: list[str]
        """
        if query is None:
            query = {}

        return [Face(record['_id'], record['image'], record['person']) for record in face_collection.find(query)]

    @staticmethod
    def delete(face_collection, object_id):
        """
        :type face_collection: Collection
        :type object_id: ObjectId
        :rtype: None
        """
        face_collection.delete_one({'_id': object_id})
