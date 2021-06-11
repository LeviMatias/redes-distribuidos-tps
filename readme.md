# TP - UDP - INTRODUCCION A REDES Y SISTEMAS DISTRIBUIDOS
---
modo de uso del TP

**Server**

```
python start-server  [-h] [-v | -q] -H ADDR -p PORT -s DIRPATH
```
donde ADDR, PORT es la address y port donde se correra el server
DIRPATH es el directorio sobre el que trabajara el server
-h, -v y -q son parametros opcionales, help, verbose y quiet respectivamente
el uso de help overridea la llamada al comando, imrpimiendo unicamente el menu de ayuda

ejemplo de uso
```
python start-server -H localhost -p 9000 -s ./lib/files-server -v
```

El server puede cerrarse en cualquier momento introduciendo por consola la letra 'q' minuscula seguida de ENTER.

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

**GoBackN**
Por default, el server y el client son desplegados en modo StopAndWait, para desplegar GBN es necesario agregar el parametro '-gbn' que activa el modo GO BACK-N tanto en server como en cliente upload o download.

La ausencia del parametro se interpreta como una peticion de uso de STOP & WAIT



ejemplo

```
 python start-server -H localhost -p 9000 -s ./lib/files-server -v -gbn

 python upload-file -H localhost -p 9000 -s ./lib/files-client/namesv1.txt -n test2.txt -v -gbn
```

---

**Detalles**

* no se maneja ni garantiza el correcto funcionamiento en el caso de dos o mas clientes operando sobre un mismo archivo en simultaneo en el servidor
