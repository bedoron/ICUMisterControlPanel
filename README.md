---
services: app-service\web,app-service
platforms: python
author: bedoron
---

# Azure Cognitive face web interface and control panel

This App service flask based deployment is intended to be a demonstration control panel for our hackathon project, 
It uses Azure Cognitive Face API in order to detect people and store them in the DB.

The application is served using Flask and makes use of Bootstrap4 and jQuery for its interface. 

In order to run this application you need to set the following variables:
* Keyvault which holds faceAPI keys
  *  KEY_VAULT_URI
  * KEY_VAULT_URL (same as above, I'm too lazy to remove it)
* Application which has access to a keyvault storing Cognitive Face API Keys: 
  * AZURE_CLIENT_ID
  * AZURE_CLIENT_SECRET
  * AZURE_TENANT_ID
* Cosmos DB Access configuration:
  * DBNAME
  * DBPASS


## Extra material
* Working website (for access contact me): http://icumistercontrolpanel.azurewebsites.net/
* Appliance code: https://github.com/bedoron/ICUMister
