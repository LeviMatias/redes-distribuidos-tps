# TP - UDP - INTRODUCCION A REDES Y SISTEMAS DISTRIBUIDOS
---
modo de uso del TP

**Server**

```
python start-server  [-h] [-v | -q] -H ADDR -p PORT -s DIRPATH
```
donde ADDR, PORT es la address y port donde se correra el server
DIRPATH es el directorio (terminado en /) sobre el que trabajara el server
-h, -v y -q son parametros opcionales, help, verbose y quiet respectivamente
el uso de help overridea la llamada al comando, imrpimiendo unicamente el menu de ayuda

ejemplo de uso
```
python start-server -H localhost -p 9000 -s ./lib/files-server/ -v
```

**Client**

```
python (upload-file | download-file)  [-h] [-v | -q] -H ADDR -p PORT [-s | -d] FILEPATH -n FILENAME
```
donde ADDR, PORT es la address y port del server
-h, -v y -q son parametros opcionales, help, verbose y quiet respectivamente
el uso de help overridea la llamada al comando, imrpimiendo unicamente el menu de ayuda

en el caso del *download*:
FILEPATH es el camino local relativo a donde se guardara el archivo
FILENAME es el nombre del archivo en el server que se desea cargar

en el caso del *upload*:
FILEPATH es el camino local relativo al archivo que se desea subir al servidor
FILENAME es el nombre del archivo con el que se desea que el server guarde lo que se va a subir

ejemplo de uso
```
 python download-file -H localhost -p 9000 -d ./lib/files-client/test1.txt -n namesv1.txt -v

 python upload-file -H localhost -p 9000 -s ./lib/files-client/namesv1.txt -n test2.txt -v
```
---

detalles:
* se configuro el TP con 10 timeouts de 0.5 secs, esto quiere decir que luego de pasados 5.5 segunds y 10 ciclos de reintento,
el programa aborta asumiendo que el destino esta offline o fuera de alcance
