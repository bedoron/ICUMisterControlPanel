import datetime
import json
import os
from _ssl import CERT_NONE

import pymongo
from bson import ObjectId
from pymongo.database import Database
from msrestazure.azure_active_directory import MSIAuthentication, ServicePrincipalCredentials

from azure.keyvault import KeyVaultClient, KeyVaultAuthentication

KEY_VAULT_URI = os.environ.get("KEY_VAULT_URI")
MONGO_URI = "mongodb://%s:%s@%s.documents.azure.com:10255/?ssl=true&replicaSet=globaldb" % (
    os.environ['DBNAME'], os.environ['DBPASS'], os.environ['DBNAME'])


def _get_kv_credentials():
    if "APPSETTING_WEBSITE_SITE_NAME" in os.environ:
        return MSIAuthentication(
            resource='https://vault.azure.net'
        )
    else:
        return ServicePrincipalCredentials(
            client_id=os.environ['AZURE_CLIENT_ID'],
            secret=os.environ['AZURE_CLIENT_SECRET'],
            tenant=os.environ['AZURE_TENANT_ID'],
            resource='https://vault.azure.net'
        )


def get_key_vault():
    """
    :rtype: KeyVaultClient
    """
    pass  # azure-keyvault is broken in Azure App Services - You need to upgrade it on the server using setup_tools
    return KeyVaultClient(_get_kv_credentials())


def get_db():
    """
    :rtype:  Database
    """
    client = pymongo.MongoClient(MONGO_URI, ssl_cert_reqs=CERT_NONE)
    return client.get_database('icumister')


if __name__ == "__main__":
    get_key_vault()


class JSONEncoder(json.JSONEncoder):
    """ extend json-encoder class"""

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)
