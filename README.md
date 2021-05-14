
Para la ejecucion de:\
 start-server\
  se requiere cumplir con los formatos obligatorios:\
   start-server -h\
   o\
   start-server -H ADDR -p PORT -s DIRPATH\
    donde -v es opcional\
    donde -H es el host\
    donde -p es el puerto\
    donde -s es el path donde el server almacena la data\
   download-file\
    se requiere cumplir con los formatos obligatorios:\
     download-file -h\
     o\
     download-file -H ADDR -p PORT -d PATH -n NAME\
      donde -v es opcional\
      donde -H es el host\
      donde -p es el puerto\
      donde -d es el path donde el server levanta la data a enviar\
      donde -n es el nombre con el que el cliente guarda el archivo descargado\
     upload-file\
      se requiere cumplir con los formatos obligatorios:\
       upload-file -h\
       o\
       upload-file -H ADDR -p PORT -d PATH -n NAME\
        donde -v es opcional\
	donde -H es el host\
	donde -p es el puerto\
	donde -d es el path donde el cliente almacena la data\
	donde -n es el nombre con el que el server guarda el archivo subido\
