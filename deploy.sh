#!/bin/bash

# stop on any error to avoid accidentally deploying with incorrect configuration
set -e

# echo commands as they are executed for easier debugging
set -x

# import the variables from the .env file
set -a
source .env
set +a

# check if the Azure App Service Plan exists, and create it if it doesn't exist
az appservice plan show --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP >/dev/null 2>&1 || \
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku $APP_SERVICE_PLAN_SKU --is-linux

# check if the Azure App Service exists, and create it if it doesn't exist
az webapp show --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP >/dev/null 2>&1 || \
az webapp create --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON:3.10"

# use a system assigned managed identity for the Azure App Service to authenticate to Azure OpenAI without needing to manage credentials
# Note: this takes a while to propagate, so if you get an error about the principal not being found in the next steps, wait a few minutes and try again
az webapp identity assign --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP

# get the managed identity principal ID for the Azure App Service to use in the role assignment for Azure OpenAI access
APP_SERVICE_PRINCIPAL_ID=$(az webapp identity show --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP --query principalId --output tsv)

# set the necessary environment variables for the app in Azure App Service to connect to Azure OpenAI 
az webapp config appsettings set --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP --settings \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
    AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true

# give the managed identity of the Azure App Service access to the Azure OpenAI resource
# if you get an error saying the principal was not found, wait a few minutes for the managed identity to propagate and try again
az role assignment create --assignee $APP_SERVICE_PRINCIPAL_ID --role "Azure AI User" --scope $FOUNDARY_PROJECT_RESOURCE_ID

# put the deployment in a subdirectory and deploy from there to avoid uploading unnecessary files
rm -rf deploy
mkdir deploy
cp *.py deploy/
cp -r static deploy/
cp -r templates deploy/
cp *.txt deploy/
cd deploy

# deploy the app to Azure App Service using the Azure CLI
az webapp up --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP --location "$AZURE_REGION" -p $APP_SERVICE_PLAN --sku $APP_SERVICE_PLAN_SKU

# cleanup the deployment directory after deployment
cd ..
rm -rf deploy