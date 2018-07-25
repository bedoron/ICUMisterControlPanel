from mongoengine import StringField, IntField
from mongoengine.document import Document


class Notification(Document):
    msg = StringField(max_length=500, required=True)
    type = StringField(max_length=50, required=True)
    time_elapsed = IntField(required=False)
    meta = {
        'collection': 'notifications',
        'ordering': ['-_id'],
        'auto_create_index': True,
        'strict': False
    }


