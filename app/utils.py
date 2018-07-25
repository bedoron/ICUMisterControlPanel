import datetime
import json
import os
from _ssl import CERT_NONE
import cognitive_face as CF
import pymongo
from bson import ObjectId
from pymongo.database import Database
from msrestazure.azure_active_directory import MSIAuthentication, ServicePrincipalCredentials

from azure.keyvault import KeyVaultClient, KeyVaultAuthentication

KEY_VAULT_URI = os.environ.get("KEY_VAULT_URI")

MONGO_DBNAME = os.environ['DBNAME']

MONGO_URI = "mongodb://%s:%s@%s.documents.azure.com:10255/?ssl=true&replicaSet=globaldb" % (
    MONGO_DBNAME, os.environ['DBPASS'], MONGO_DBNAME)

KNOWN_PERSON_GROUP = "HackathonPersonGroup"
UNKNOWN_PERSON_GROUP = "UnknownHackathonPersonGroup"
IGNORE_PERSON_GROUP = "IgnoreHackathonPersonGroup"


def _get_kv_credentials():
    # if "APPSETTING_WEBSITE_SITE_NAME" in os.environ:
    #     return MSIAuthentication(
    #         resource='https://vault.azure.net'
    #     )
    # else:
    #     return ServicePrincipalCredentials(
    #         client_id=os.environ['AZURE_CLIENT_ID'],
    #         secret=os.environ['AZURE_CLIENT_SECRET'],
    #         tenant=os.environ['AZURE_TENANT_ID'],
    #         resource='https://vault.azure.net'
    #     )
    return ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'],
        secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant=os.environ['AZURE_TENANT_ID'],
        resource='https://vault.azure.net'
    )


def _get_key_vault():
    """
    :rtype: KeyVaultClient
    """
    pass  # azure-keyvault is broken in Azure App Services - You need to upgrade it on the server using setup_tools
    return KeyVaultClient(_get_kv_credentials())


kvclient = _get_key_vault()


def get_secret(secret_id):
    return kvclient.get_secret(KEY_VAULT_URI, secret_id, '').value


def create_person_group_if_needed(person_group_name):
    try:
        CF.person_group.create(person_group_name.lower(), person_group_name)
    except Exception as e:
        pass


def initialize_cf():
    cf_secret = get_secret('faceKey1')
    CF.Key.set(cf_secret)
    CF.BaseUrl.set('https://westeurope.api.cognitive.microsoft.com/face/v1.0')
    for face_group_name in [UNKNOWN_PERSON_GROUP, KNOWN_PERSON_GROUP, IGNORE_PERSON_GROUP]:
        create_person_group_if_needed(face_group_name)


def setup_mongoengine(app):
    app.config['MONGODB_SETTINGS'] = {
        'host': MONGO_URI,
        'db': MONGO_DBNAME
    }


def get_db():
    """
    :rtype:  Database
    """
    client = pymongo.MongoClient(MONGO_URI, ssl_cert_reqs=CERT_NONE)
    return client.get_database('icumister')


if __name__ == "__main__":
    _get_key_vault()


class JSONEncoder(json.JSONEncoder):
    """ extend json-encoder class"""

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


class EventHubClient(object):
    connection_template = {
        'headers': {
            'Authorization': 'SharedAccessSignature ' +
                             'sr={namespace}.servicebus.windows.net&' +
                             'sig={shared_access_key}&' +
                             'se={ts}&' +
                             'skn={policy_name}',

            'Content-Type': 'application/atom+xml;type=entry;charset=utf-8',
            'url': 'https://{namespace}.servicebus.windows.net/{name}/messages'
        }
    }

    def __init__(self, kv_client):
        super(EventHubClient, self).__init__()
        self._kv_client = kv_client
