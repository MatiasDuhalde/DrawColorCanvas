import threading
import json
import socket
from color_canvas import Canvas


class Servidor:

    def __init__(self, host, port):
        print("Inicializando servidor...")
        # Crear el objeto Canvas
        self.canvas = Canvas(50, 50)
        self.host = host
        self.port = port

        # Crear un socket IPv4, TCP
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Ligar socket al host y al puerto del servidor
        self.socket_server.bind((self.host, self.port))

        # Activar escuchar en el socket
        self.socket_server.listen()
        print(f"Servidor escuchando en {self.host}:{self.port}")
        print("Servidor aceptando conexiones!")

        # Diccionario que contendrá los sockets de multiples clientes
        self.sockets_clientes = dict()

        # ============================ ADVERTENCIA ============================
        # Si se implementa el método conectar_varios_clientes, cambiar este
        # valor a False para recibir múltiples clientes.
        self.un_cliente = False

        # El servidor verifica automáticamente si se aceptará uno o
        # varios clientes y ejecuta la función correspondiente en un Thread.
        if self.un_cliente:
            funcion_target = self.conectar_un_cliente
        else:
            funcion_target = self.conectar_varios_clientes
        thread = threading.Thread(target=funcion_target, daemon=True)
        thread.start()

    def conectar_un_cliente(self):
        """
        Permite que el servidor maneje un solo cliente durante su ejecución.
        """
        # ============================= COMPLETAR =============================
        socket_cliente, _ = self.socket_server.accept()
        print("Ha llegado un nuevo cliente!")
        self.escuchar_cliente(socket_cliente)
        # =====================================================================

    def escuchar_cliente(self, socket_cliente, id_cliente=0):
        """
        Permite que el servidor escuche los mensajes de un cliente.
        El socket de dicho cliente se encuentra en la variable socket_cliente.
        Para el caso de múltiples clientes, también se recibe id_cliente
        Debes procesar el mensaje enviado y generar una respuesta que
        posteriormente será enviada.
        """
        try:
            # =========================== COMPLETAR ===========================
            while True:
                # Recibir largo del mensaje
                largo_mensaje_bytes = socket_cliente.recv(5)
                # Decodificar largo
                largo_mensaje = int.from_bytes(largo_mensaje_bytes, byteorder="little")

                # Recibir resto del mensaje
                mensaje_bytes = bytearray()
                while len(mensaje_bytes) < largo_mensaje:
                    tamano_chunk = min(largo_mensaje - len(mensaje_bytes), 128)
                    mensaje_bytes += socket_cliente.recv(tamano_chunk)

                # Decodificar mensaje con JSON
                json_recibido = json.loads(mensaje_bytes.decode())

                # self.manejar_mensaje(socket_cliente, id_cliente, json_recibido)
                if json_recibido["comando"] == "cerrar":
                    break
                if json_recibido["comando"] == "pintar":
                    # Cambiar color pixel
                    self.canvas.pintar_pixel(json_recibido)

                # Crear mensaje de respuesta
                respuesta = self.canvas.obtener_tablero()

                # Enviar la respuesta
                self.enviar_respuesta(socket_cliente, respuesta)
            # =================================================================
        except ConnectionResetError:
            print("Error de conexión con el cliente!")
        finally:
            mensaje = {"cerrar" : True}
            self.enviar(socket_cliente, mensaje)
            socket_cliente.close()
            if id_cliente == 0:
                print("Cerrando conexión con el cliente...")
            else:
                print(f"Cerrando conexión con el cliente {id_cliente}...")
                if self.sockets_clientes.get(id_cliente):
                    del self.sockets_clientes[id_cliente]
                    print(f"Se ha eliminado el socket del cliente {id_cliente}.")

    def enviar_respuesta(self, socket_cliente, respuesta):
        """
        Recibe el socket del cliente que envió el mensaje, y un diccionario
        que contiene la respuesta a enviar.
        Si sólo se implementó una conexión, se envía al cliente en socket_cliente
        Si hay múltiples clientes, se envía a todos sus sockets.
        """
        if self.un_cliente:
            self.enviar(socket_cliente, respuesta)
        else:
            self.enviar_a_todos(respuesta)

    def enviar(self, socket_cliente, mensaje):
        """
        Recibe un socket y un diccionario. El diccionario debe ser codificado,
        y enviado al socket.
        """
        # ============================= COMPLETAR =============================
        # Create json and encode mensaje
        mensaje_json = json.dumps(mensaje)
        mensaje_bytes = mensaje_json.encode()
        # Get message length
        largo_mensaje_bytes = len(mensaje_bytes).to_bytes(5, byteorder="little")
        # Send mensaje to server
        socket_cliente.send(largo_mensaje_bytes + mensaje_bytes)
        # =====================================================================

    # =========================================================================
    # ========================= SECCION MULTI-CLIENTE =========================
    def conectar_varios_clientes(self):
        """
        Permite que el servidor acepte paralelamente múltiples conexiones de
        varios clientes.
        Este método solo se usa en el caso de múltiples clientes.
        """
        # ============================= COMPLETAR =============================
        # Llevar cuenta de la cantidad de clientes conectados
        id_cliente = 1
        while True:
            # Aceptar cliente
            socket_cliente, _ = self.socket_server.accept()
            print(f"Ha llegado un nuevo cliente con id {id_cliente}!")

            # Guardar nuevo socket en diccionario
            self.sockets_clientes[id_cliente] = socket_cliente

            # Iniciar un thread del cliente
            thread_cliente = threading.Thread(
                target=self.escuchar_cliente,
                args=(socket_cliente, id_cliente),
                daemon=True)
            thread_cliente.start()

            print(f"Escuchando a cliente {id_cliente}!")
            # Incrementar la id
            id_cliente += 1
        # =====================================================================

    ## IMPLEMENTADO
    def enviar_a_todos(self, mensaje):
        """
        Envía el mensaje a todos los sockets actualmente conectados.
        Este método solo se usa en el caso de múltiples clientes.
        """
        # No usar diccionario directamente, así se previene
        # RuntimeError: dictionary changed size during iteration
        ids_cliente = list(self.sockets_clientes.keys())
        for id_cliente in ids_cliente:
            try:
                self.enviar(self.sockets_clientes[id_cliente], mensaje)
            except ConnectionResetError:
                print(f"El cliente {id_cliente} ha sido desconectado! (enviar_a_todos)")
                if self.sockets_clientes.get(id_cliente):
                    del self.sockets_clientes[id_cliente]
                    print(f"Se ha eliminado el socket del cliente {id_cliente}.")
            except ConnectionAbortedError:
                print(f"El cliente {id_cliente} ha sido desconectado! (enviar_a_todos)")
                if self.sockets_clientes.get(id_cliente):
                    del self.sockets_clientes[id_cliente]
                    print(f"Se ha eliminado el socket del cliente {id_cliente}.")
                print('Error de conexion con cliente')
            except IndexError:
                print(f"El cliente {id_cliente} no se encuentra en el diccionario.")
