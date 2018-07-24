from eventhub_client import NotificationHubClient
from model.notification import Notification


class NotifierREST(object):
    def __init__(self, connection_string):
        super(NotifierREST, self).__init__()
        self._connection_string = connection_string

    def notify(self, notification):
        """
        :type notification: Notification
        """
        hub = NotificationHubClient(self._connection_string, "ICUMisterNotificationHub", debug=True)
        payload = {
            'data': notification.to_eventhub_json()
        }

        hub.send_gcm_notification(payload)
