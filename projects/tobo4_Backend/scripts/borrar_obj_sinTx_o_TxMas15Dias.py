import datetime
import requests, json
from datetime import datetime, timedelta

def getGlobalObjects():
  url = "https://appv2.huntertrack.com.do/api/core/object" 
  payload = {}
  headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50SWQiOjMsImFjY291bnRJZHMiOlszXSwidXNlcklkIjoyMDc3NywibmFtZSI6IkpQIiwibmlja25hbWUiOiJqcHNjcmlwdHMiLCJyb2xlIjoyLCJ3ZWIiOmZhbHNlLCJleHAiOjE3MjU3NjgwMDAsImNsaWVudElkIjoxNCwiY2xpZW50SWRzIjpbMTRdLCJpcCI6bnVsbCwic2Vzc2lvbklkIjoiYjVkZTA3NzItZDZlYy00NWJiLWE3OTctOTgwNDM0OTgzMTg0IiwiZGV2aWNlSWQiOiJiNWRlMDc3Mi1kNmVjLTQ1YmItYTc5Ny05ODA0MzQ5ODMxODQiLCJpYXQiOjE3MjQ5MzgyNDR9.xYMbpUUtNRzjd1JegTPa4oHiIqVqDP-8kaCglbPnbuk'
  }
  response = requests.request("GET", url, headers=headers, data=payload)
  datos = json.loads(response.text)
  return datos

def getLastPointForId(id):
  url = "https://appv2.huntertrack.com.do/api/reports/last-point/by-id?id="+str(id)
  payload = {}
  headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50SWQiOjMsImFjY291bnRJZHMiOlszXSwidXNlcklkIjoyMDc3NywibmFtZSI6IkpQIiwibmlja25hbWUiOiJqcHNjcmlwdHMiLCJyb2xlIjoyLCJ3ZWIiOmZhbHNlLCJleHAiOjE3MjU3NjgwMDAsImNsaWVudElkIjoxNCwiY2xpZW50SWRzIjpbMTRdLCJpcCI6bnVsbCwic2Vzc2lvbklkIjoiYjVkZTA3NzItZDZlYy00NWJiLWE3OTctOTgwNDM0OTgzMTg0IiwiZGV2aWNlSWQiOiJiNWRlMDc3Mi1kNmVjLTQ1YmItYTc5Ny05ODA0MzQ5ODMxODQiLCJpYXQiOjE3MjQ5MzgyNDR9.xYMbpUUtNRzjd1JegTPa4oHiIqVqDP-8kaCglbPnbuk'
  }  
  response = requests.request("GET", url, headers=headers, data=payload)
  dato = response.text
  dato = dato.replace("'","\"")
  datos = json.loads(dato)
  return datos

def deleteObject(id):
  url = "https://appv2.huntertrack.com.do/api/core/object?id="+str(id) 
  payload = {}
  headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50SWQiOjMsImFjY291bnRJZHMiOlszXSwidXNlcklkIjoyMDc3NywibmFtZSI6IkpQIiwibmlja25hbWUiOiJqcHNjcmlwdHMiLCJyb2xlIjoyLCJ3ZWIiOmZhbHNlLCJleHAiOjE3MjU3NjgwMDAsImNsaWVudElkIjoxNCwiY2xpZW50SWRzIjpbMTRdLCJpcCI6bnVsbCwic2Vzc2lvbklkIjoiYjVkZTA3NzItZDZlYy00NWJiLWE3OTctOTgwNDM0OTgzMTg0IiwiZGV2aWNlSWQiOiJiNWRlMDc3Mi1kNmVjLTQ1YmItYTc5Ny05ODA0MzQ5ODMxODQiLCJpYXQiOjE3MjQ5MzgyNDR9.xYMbpUUtNRzjd1JegTPa4oHiIqVqDP-8kaCglbPnbuk'
  }
  response = requests.request("DELETE", url, headers=headers, data=payload)
  datos = json.loads(response.text)
  return datos

# 1. Se asigna id del cliente que se va a procesar:
client_id = 29

# Consume método que devuelve registros de todos los objetos existentes:
globalObjects = getGlobalObjects()
print("Cargó Objetos globales...")
for row in globalObjects:
  # Filtra los objetos que son del Cliente procesado:
  if(row['clientId'] == client_id):
    id = row['id']
    fecha_punto = ''
    # Consume método que recupera los últimos_puntos de los objetos del cliente:
    last_point = getLastPointForId(id)
    # Si no tiene registro en UltimoPunto, consume el método para borrar el objeto:
    if(last_point == [] or last_point == ""):
      #pass
      # print("id: ", id, "last_point: ", last_point)
      borrar_objeto = deleteObject(id)
      print("borrar: ", borrar_objeto)
    else:
      #pass
      # Si la fecha del UltimoPunto es nula, consume el método para borrar el objeto:
      if(last_point[0]['statusDate'] == None):
        borrar_objeto = deleteObject(id)
        print("borrar: ", borrar_objeto)
        #pass
      else:
        # Compara la fecha del UltimoPunto con la fecha actual:
        fecha_punto = last_point[0]['point']['eventDate']['date']
        fec_act = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S.%f%z')
        hoy = datetime.strptime(fec_act+"Z", '%Y-%m-%dT%H:%M:%S.%f%z')
        fec_pto = datetime.strptime(fecha_punto, '%Y-%m-%dT%H:%M:%S.%f%z')
        diferencia = hoy-fec_pto
        dif = ({diferencia.days}.pop())
        # Si la diferencia es mayor a 15 días, consume el método para borrar el objeto:
        if(dif > 15):
          print("object_id: ",id, "Diferencia: ", dif)
          borrar_objeto = deleteObject(id)
        else:
          pass

print("Proceso finalizado...")

