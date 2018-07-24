from mongoengine import URLField, StringField
from mongoengine.document import Document


class Notification(Document):
    url = URLField(required=True)
    msg = StringField(max_length=500, required=True)

    meta = {
        'collection': 'notifications',
        'ordering': ['-_id'],
        'auto_create_index': True,
        'strict': False
    }
