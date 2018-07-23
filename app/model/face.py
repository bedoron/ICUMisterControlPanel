from pymongo.collection import Collection, ObjectId


class Face(object):
    """
    Face document should look as following:
    {
        "_id": <mongo object id>
        "image": binary file data
    }
    """

    def __init__(self, id, image):
        super(Face, self).__init__()
        self._id = id
        self._image = image

    def read(self):
        return self._image

    @property
    def image(self):
        return self._image

    @property
    def id(self):
        return self._id

    @staticmethod
    def create(face_collection, binary_image):
        """
        :type face_collection: Collection
        :type binary_image: bytearray
        :rtype: Face
        """
        result = face_collection.insert_one({'image': binary_image})
        return Face(result.inserted_id, binary_image)

    @staticmethod
    def find(face_collection, object_id):
        """
        :type face_collection: Collection
        :type object_id: ObjectId
        :rtype: Face
        """
        face_document = face_collection.find_one({'_id': object_id})
        return Face(face_document['id'], face_document['image']) if face_document else None
