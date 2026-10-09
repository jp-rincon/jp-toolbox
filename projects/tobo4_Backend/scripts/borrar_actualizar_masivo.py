import requests
import json
import time

def deleteDevice(id):
  url = "https://appv2.huntertrack.com.do/api/core/device?id="+str(id) 
  payload = {}
  headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50SWQiOjMsImFjY291bnRJZHMiOlszXSwidXNlcklkIjoyMDc3NywibmFtZSI6IkpQIiwibmlja25hbWUiOiJqcHNjcmlwdHMiLCJyb2xlIjoyLCJ3ZWIiOmZhbHNlLCJleHAiOjE3MjY5Nzc2MDAsImNsaWVudElkIjoxNCwiY2xpZW50SWRzIjpbMTRdLCJpcCI6bnVsbCwic2Vzc2lvbklkIjoiZjYyN2Y0MGEtZDYxNy00NGI2LWJmNjYtYTMxNDg4OTM3NzQzIiwiZGV2aWNlSWQiOiJmNjI3ZjQwYS1kNjE3LTQ0YjYtYmY2Ni1hMzE0ODg5Mzc3NDMiLCJpYXQiOjE3MjU4MTA2NzZ9.xkGicq9nUxaa4wx9tx0DNtIfb796Wd8kiaKw2cMjICU'
  }
  response = requests.request("DELETE", url, headers=headers, data=payload)
  datos = json.loads(response.text)
  return datos

def deleteObject(id):
  url = "https://appv2.huntertrack.com.do/api/core/object?id="+str(id) 
  payload = {}
  headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50SWQiOjMsImFjY291bnRJZHMiOlszXSwidXNlcklkIjoyMDc3NywibmFtZSI6IkpQIiwibmlja25hbWUiOiJqcHNjcmlwdHMiLCJyb2xlIjoyLCJ3ZWIiOmZhbHNlLCJleHAiOjE3MjY5Nzc2MDAsImNsaWVudElkIjoxNCwiY2xpZW50SWRzIjpbMTRdLCJpcCI6bnVsbCwic2Vzc2lvbklkIjoiZjYyN2Y0MGEtZDYxNy00NGI2LWJmNjYtYTMxNDg4OTM3NzQzIiwiZGV2aWNlSWQiOiJmNjI3ZjQwYS1kNjE3LTQ0YjYtYmY2Ni1hMzE0ODg5Mzc3NDMiLCJpYXQiOjE3MjU4MTA2NzZ9.xkGicq9nUxaa4wx9tx0DNtIfb796Wd8kiaKw2cMjICU'
  }
  response = requests.request("DELETE", url, headers=headers, data=payload)
  datos = json.loads(response.text)
  return datos

def updateObject(obj_id, client_id):
  url = "https://appv2.huntertrack.com.do/api/core/object/change-client"
  payload = json.dumps({
    "id": obj_id, 
    "clientId": client_id
  })
  headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50SWQiOjMsImFjY291bnRJZHMiOlszXSwidXNlcklkIjoyMDc3NywibmFtZSI6IkpQIiwibmlja25hbWUiOiJqcHNjcmlwdHMiLCJyb2xlIjoyLCJ3ZWIiOmZhbHNlLCJleHAiOjE3MjY5Nzc2MDAsImNsaWVudElkIjoxNCwiY2xpZW50SWRzIjpbMTRdLCJpcCI6bnVsbCwic2Vzc2lvbklkIjoiZjYyN2Y0MGEtZDYxNy00NGI2LWJmNjYtYTMxNDg4OTM3NzQzIiwiZGV2aWNlSWQiOiJmNjI3ZjQwYS1kNjE3LTQ0YjYtYmY2Ni1hMzE0ODg5Mzc3NDMiLCJpYXQiOjE3MjU4MTA2NzZ9.xkGicq9nUxaa4wx9tx0DNtIfb796Wd8kiaKw2cMjICU',
  }
  response = requests.request("PUT", url, headers=headers, data=payload)
  return response.text

print("Inicia proceso. Llena array...")
ids = [85378, 85380, 85384, 85821, 85981, 86411, 87177, 118775]
## Acá se coloca el listado de Id's de Equipos u Objetos a Borrar o Actualizar:
# [85378, 85380, 85384, 85821, 85981, 86411, 87177, 118775]

print("IDS: ", ids)

id=''
#client_id = 20208

for value in ids:
  id = value
  print("id: ", id)
  ## Para actualizar id_cliente del objeto:
  # actualizar = updateObject(obj_id, client_id)
  # print(actualizar)
  ## Para Borrar un equipo:
  # borrar = deleteDevice(id)
  ## Para Borrar Objeto:
  borrar = deleteObject(id)
  print(borrar)
  time.sleep(15)

print("Proceso finalizado...")
