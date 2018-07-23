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

    def __init__(self, id, encoded_image):
        super(Face, self).__init__()
        self._id = id
        self._image = base64.b64decode(encoded_image)

    def read(self):
        return self._image

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
    def create(face_collection, binary_image):
        """
        :type face_collection: Collection
        :type binary_image: bytearray
        :rtype: Face
        """
        encoded_file = base64.b64encode(binary_image)
        result = face_collection.insert_one({'image': encoded_file})
        return Face(result.inserted_id, encoded_file)

    @staticmethod
    def find(face_collection, object_id):
        """
        :type face_collection: Collection
        :type object_id: ObjectId
        :rtype: Face
        """
        face_document = face_collection.find_one({'_id': object_id})
        return Face(face_document['_id'], face_document['image']) if face_document else None

    @staticmethod
    def find_all(face_collection, query=None):
        """
        :type face_collection: Collection
        :type query: dict
        :rtype: list[str]
        """
        if query is None:
            query = {}

        return [record['_id'] for record in face_collection.find(query)]


    @staticmethod
    def delete(face_collection, object_id):
        """
        :type face_collection: Collection
        :type object_id: ObjectId
        :rtype: None
        """
        face_collection.delete_one({'_id': object_id})
