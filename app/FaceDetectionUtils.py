import cognitive_face as CF

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FaceDetectionUtils(object):
    """
    :rtype: list
    """
    @staticmethod
    def detect_faces_from_jpeg(face_image):
        result = CF.face.detect(face_image, face_id=True, attributes="gender,age")
        return result
