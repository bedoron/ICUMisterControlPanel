import datetime

from flask import url_for
from mongoengine import StringField, DictField
from mongoengine.document import Document


class Notification(Document):
    icum_face_id = StringField(requred=False)
    msg = StringField(max_length=500, required=True)
    msg_type = StringField(max_length=15, required=False)
    attributes = DictField()

    meta = {
        'collection': 'notifications',
        'ordering': ['-_id'],
        'auto_create_index': True,
        'strict': False
    }

    def to_eventhub_json(self):
        res = {
            'url': 'http://icumistercontrolpanel.azurewebsites.net' + url_for('show_notification', notification_id=str(self.id)),
            'msg': self.msg,
            'type': self.msg_type if self.msg_type else 'unknown',
            'timestamp': str(datetime.datetime.now()),
            'time_elapsed': 5
        }
        return res
