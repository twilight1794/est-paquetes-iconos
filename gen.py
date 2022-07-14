#!/usr/bin/env python3
import os, json, re
import xml.etree.ElementTree as ET
import requests

reg = re.compile("ComponentInfo\{(.+)/(.+)\}")

#class SetEncoder(json.JSONEncoder):
#  def default(self, obj):
#    if isinstance(obj, set):
#      return list(obj)
#    return json.JSONEncoder.default(self, obj)

with open("conf.json") as fi:
  ji = json.load(fi)

for k in ji["repos"]:
  print("Descargando índice "+k)
  r = requests.get(ji["repos"][k][1])
  if not (r.status_code == 200 and r.headers["Content-Type"] in ("application/xml", "text/xml")):
    raise ValueError("Code: %s, type: %s"%(r.status_code, r.headers["Content-Type"]))
  ji["repos"][k].append(set())
  for c in ET.fromstring(r.text):
    if c.tag == "application":
      ji["repos"][k][2].update([c.attrib["id"]])

for k in ji["packs"]:
  print("Descargando appfilter "+k)
  r = requests.get(ji["packs"][k][1])
  if not (r.status_code == 200):
    raise ValueError("Code: %s"%r.status_code)
  ji["packs"][k].append({})
  for c in ET.fromstring(r.text):
    if c.tag == "item" and not c.attrib["component"].startswith(":"):
      co = re.fullmatch(reg, c.attrib["component"])
      if not co:
        print("Ignorando %s"%c.attrib["component"])
        continue
      ci = co.groups()
      if not ci[0] in ji["packs"][k][2]:
        ji["packs"][k][2][ci[0]] = set()
      ji["packs"][k][2][ci[0]].update([ci[1]])

#with open("ZZ.json", "w") as w:
#  json.dump(ji, w, cls=SetEncoder)

data = {}
for k_repo in ji["repos"]:
  data[k_repo] = {}
  for k_package in ji["repos"][k_repo][2]:
    # Marcar paquetes que no existen en un pack
    #inex = {}
    #for k_pack in ji["packs"]:
    #  inex[k_pack] = true
    data[k_repo][k_package] = {}
    for k_pack in ji["packs"]:
      if k_package in ji["packs"][k_pack][2]:
        for k_act in ji["packs"][k_pack][2][k_package]:
          if not k_act in data[k_repo][k_package]:
            data[k_repo][k_package][k_act] = {}
          data[k_repo][k_package][k_act][k_pack] = True
      #else:
      #  inex[k_pack] = false
    # Tratar inexistentes por pack
    for k_act in data[k_repo][k_package]:
      for k_pack in ji["packs"]:
        if data[k_repo][k_package][k_act].get(k_pack, False) == False:
          data[k_repo][k_package][k_act][k_pack] = False
    # Tratar inexistentes totales
    if len(data[k_repo][k_package]) == 0:
      data[k_repo][k_package]["_"] = {}
      for k_pack in ji["packs"]:
        data[k_repo][k_package]["_"][k_pack] = False

try:
  os.chdir("data")
except FileNotFoundError:
  os.mkdir("data")
  os.chdir("data")
finally:
  l = os.listdir()
  l.sort()
  if len(l) > 0:
    os.rename("latest.json", "%04d.json"%len(l))
  with open("latest.json", "w") as w:
    json.dump(data, w)

"""
Plan:
1- Obtener índices y appfilters de conf.json
2- Almacenar lista de paquetes de indices ["repos"][repo][2]: [packages]
3- Almacenar lista de actividades de appfilters ["packs"][pack][2][package]: [activity]
4. Por cada índice
  a. Por cada programa de índice
    I. Por cada appfilter
      A. Si existe el paquete en el appfilter, rellenar las filas por actividad
      B. Eliminar el paquete del indice y del appfilter

 json.dumps(json_object, sort_keys=True)

input.json[repos]: repo>2>package
input.json[packs]: pack>2>package>activity
data.json: repo>package>activity>pack
"""
