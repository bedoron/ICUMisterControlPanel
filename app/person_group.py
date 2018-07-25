import time

from cognitive_face import CognitiveFaceException
from utils import KNOWN_PERSON_GROUP, IGNORE_PERSON_GROUP, UNKNOWN_PERSON_GROUP
import cognitive_face as CF
from model.personlegacy import PersonLegacy


class PersonGroup(object):
    def __init__(self, pg_name):
        super(PersonGroup, self).__init__()

        self._person_group_name = pg_name  # type: str
        self._person_group_id = pg_name.lower()

    @staticmethod
    def reset_all():
        CF.util.clear_person_groups()
        time.sleep(1)
        PersonGroup.create_known_person_group()
        time.sleep(1)
        PersonGroup.create_unknown_person_group()
        time.sleep(1)
        PersonGroup.create_ignore_person_group()

    @staticmethod
    def create(person_group_name):
        CF.person_group.create(person_group_name.lower(), person_group_name)
        return PersonGroup(person_group_name)

    @classmethod
    def create_known_person_group(cls):
        return cls.create(KNOWN_PERSON_GROUP)

    @classmethod
    def create_unknown_person_group(cls):
        return cls.create(UNKNOWN_PERSON_GROUP)

    @classmethod
    def create_ignore_person_group(cls):
        return cls.create(IGNORE_PERSON_GROUP)

    @classmethod
    def known_person_group(cls):
        return cls(KNOWN_PERSON_GROUP)

    @classmethod
    def unknown_person_group(cls):
        return cls(UNKNOWN_PERSON_GROUP)

    @classmethod
    def ignore_person_group(cls):
        return cls(IGNORE_PERSON_GROUP)

    @property
    def name(self):
        return self._person_group_name

    def reset(self):
        CF.person_group.delete(self._person_group_id)
        time.sleep(CF.util.TIME_SLEEP)
        CF.person_group.create(self._person_group_id, self._person_group_name)
        time.sleep(CF.util.TIME_SLEEP)

    def remove_person(self, person):
        """
        :type person: PersonLegacy
        """
        if not self.has_person(person):
            return False

        CF.person.delete(self._person_group_id, person.get_group_person_id(self._person_group_name))
        person.remove_trained_details(self._person_group_name)

        return True

    def add_person(self, person):
        """
        :type person: PersonLegacy
        :raises CognitiveFaceException:
        """
        if self.has_person(person):
            return False

        person_result = CF.person.create(self._person_group_id, str(person.id))
        person_id = person_result['personId']

        # this part might raise CognitiveFaceException
        persistent_face_id = CF.person.add_face(person, self._person_group_id, person_id)
        CF.person_group.train(self._person_group_id)
        person.add_trained_details(person_id, persistent_face_id, self._person_group_name)

        return True

    def identify(self, face_ids):
        """
        :type face_ids: list
        :rtype: dict
        """
        try:
            identified = CF.face.identify(face_ids, self._person_group_id)
            # actually_identified = filter(lambda record: record['faceId'] in person.detected_ids, identified)
            return {record['faceId']: record['candidates'] for record in identified}
        except CognitiveFaceException as ex:
            if ex.status_code not in [404, 400]:
                raise ex

        return None

    def has_person(self, person):
        """
        :rtype person: Person
        """
        identified = self.identify(person)
        return all([len(candidates) != 0 for candidates in identified.values()]) if identified else False

    def __contains__(self, person):
        if not isinstance(person, PersonLegacy):
            raise TypeError()

        return self.has_person(person)
