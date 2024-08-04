# Overview

# ControllerProcess and ClientProcess ExampleControllerProcess and ExampleClientProcess
# are classes used to facilitate inter-process communication using shared memory and
# method registration.

# Classes and Usage

# **SharedProcessBase** is a base class that provides methods for interacting with
# shared memory.
# It should not be instantiated directly but inherited by other process classes.

# Methods
# register_method(method_name, method): Registers a method that can be called remotely by other processes.
# get_data(key): Retrieves data from shared memory associated with the given key.
# list_data(): Lists all items in the shared memory.
# set_data(key, value): Sets data in the shared memory.
# delete_data(key): Deletes data from the shared memory associated with the given key.
# call_remote_method(method_name): Calls a registered method on the shared object.

# **ControllerProcess** is a class that manages shared memory and interacts with
# ClientProcess. It inherits from SharedProcessBase.

# Initialization
# init(client_process_class, port_number=50000, authkey=b'secret'): Initializes the controller process and connects to the shared manager.
# Methods
# launch_client_process(config): Launches ClientProcess with the provided configuration.
# is gonna call the ClientProcess run method and that will have access to the config as self.config
# terminate_client_process(): Terminates the client process.
# terminate_shared_manager(): Terminates the shared manager.
# cleanup(): Terminates both that client process and the manager

# **ClientProcess** is a class that interacts with shared memory and can call methods
# on ControllerProcess. It inherits from SharedProcessBase as well.

# Initialization
# init(config, port_number=50000, authkey=b'secret'): Initializes the client process and connects to the shared manager.
# Methods
# run(): Main method to run the ClientProcess. This method should be overridden in subclasses.

# **Example Usage**
#

# class ExampleClientProcess(ClientProcess):
#     """
#     ExampleClientProcess is a secondary process that interacts with shared memory and can call methods on ControllerProcess.
#     """
#     def run(self):
#         """
#         Main Method to run the ExampleClientProcess
#         """
#         print("ExampleClientProcess is running with config:", self.config)
#         self.shared_object.set_data('process_b_data', 'Data from ExampleClientProcess')
#         self.shared_object.call_method('reload')
#         self.shared_object.call_method('method_with_params', 'param1_value', 'param2_value')

# class ExampleControllerProcess(ControllerProcess):
#     def __init__(self, client_process_class, port_number=50000, authkey=b'secret'):
#         super().__init__(client_process_class, port_number, authkey)
#         self.register_method('reload', self.reload)
#         self.register_method('custom_method', self.custom_method)
#         self.register_method('method_with_params', self.method_with_params)

#     def reload(self):
#         print("ExampleControllerProcess is reloading...")

#     def custom_method(self):
#         print("Custom data", self.get_data("process_b_data"))
#         print("Custom method in ExampleControllerProcess called.")

#     def method_with_params(self, param1, param2):
#         print(f"Method with params called with: {param1}, {param2}")

# if __name__ == '__main__':

#     example_controller = ExampleControllerProcess(ExampleClientProcess)

#     example_controller.launch_client_process(<some configuration, will be used in the run method of the ClientProcess>)
#     time.sleep(2)  # Give ClientProcess time to start

#     example_controller.list_data()  # List all items in the shared memory
#     example_controller.client_process.list_data()  # same thing
#     example_controller.client_process.call_method('custom_method')  # Simulate ClientProcess calling a custom method from the parent
#     example_controller.get_data('process_b_data')  # Example of deleting data from shared memory
#     example_controller.cleanup()  # Cleanup when needed


import multiprocessing
import socket
import threading
import pickle
import time
import os
from multiprocessing import Process
from multiprocessing.context import AuthenticationError
import socket
import atexit

# All Processes
from multiprocessing.managers import BaseManager


# class ProcessShareManager(BaseManager):
#     """
#     Custom manager class that allows the sharing of complex objects
#     between processes using the multiprocessing.managers.BaseManager.
#     """
#     pass

# class ProcessSharedObject:
#     """
#     Manages shared data and methods between processes.

#     Attributes:
#         data (dict): A dictionary to store shared data.
#         process_methods (dict): A dictionary to store registered methods
#     """
#     def __init__(self):
#         self.data = {}
#         self.methods = {}

#     def set_data(self, key, value):
#         self.data[key] = value

#     def get_data(self, key):
#         return self.data.get(key, None)

#     def list_keys(self):
#         return self.data.keys()

#     def list_data(self):
#         return self.data.items()

#     def has_data(self, key) -> bool:
#         return key in self.data

#     def delete_data(self, key) -> bool:
#         """
#         Returns:
#             bool: True if the key was deleted, False if the key was not found.
#         """
#         return self.data.pop(key, None) is not None

#     def call_method(self, method_name, *args, **kwargs):
#         """
#         Calls a registered method
#         """
#         if method_name in self.methods:
#             self.methods[method_name](*args, **kwargs)
#         else:
#             print(f"Method {method_name} not found.")

#     def register_method(self, method_name, method):
#         self.methods[method_name] = method

#     @staticmethod
#     def connect_to_shared_manager(port_number=50000):
#         """
#         Connects to the shared manager server and returns the shared object.
#         """
#         try:
#             ProcessShareManager.register('get_shared_object')
#             manager = ProcessShareManager(address=('localhost', port_number), authkey=b'secret')
#             manager.connect()
#             shared_object = manager.get_shared_object()
#             return shared_object
#         except Exception as e:
#             print(f"ProcessSharedObject: Failed to connect to shared manager server: {e}")
#             return None

#     @staticmethod
#     def start_shared_manager(port_number=50000):
#         """
#         Starts the shared manager server
#         """
#         # Server-Side Registration of get_shared_object:
#         ProcessShareManager.register('get_shared_object', ProcessSharedObject)
#         assert 'get_shared_object' in ProcessShareManager._registry, "Callable not registered correctly"

#         manager = ProcessShareManager(address=('', port_number), authkey=b'secret')
#         try:
#             server = manager.get_server()
#             print("ProcessSharedObject: Shared Manager Server running...")
#             server.serve_forever()
#         except OSError as e:
#             if e.errno == 98:
#                 print(f"ProcessSharedObject: Port {port_number} is already in use. Attempting to connect...")
#                 shared_object = ProcessSharedObject.connect_to_shared_manager(port_number)
#                 # shared_object = connect_to_shared_manager(port_number)
#                 if shared_object:
#                     print("Successfully connected to the existing shared manager server. Please connect.")
#                 else:
#                     print(f"Failed to connect to the shared manager server: {e}")
#             else:
#                 print(f"Failed to start shared manager server: {e}")
#         except Exception as e:
#             print(f"Failed to initialize shared manager server: {e}")


class ProcessSharedObject:
    def __init__(self, host='localhost', port=50000):
        self.host = host
        self.port = port
        self.data = {}
        self.methods = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        self.stop_event = threading.Event()
        self.printer_thread = threading.Thread(target=self.print_data_periodically)
        self.printer_thread.daemon = True
        self.printer_thread.start()

    def handle_client(self, client_socket):
        with client_socket:
            while True:
                try:
                    request = client_socket.recv(4096)
                    if not request:
                        break
                    command, *args = pickle.loads(request)
                    response = self.process_command(command, *args)
                    client_socket.sendall(pickle.dumps(response))
                except EOFError:
                    break
                except Exception as e:
                    client_socket.sendall(pickle.dumps(f"Error: {e}"))
                    break

    def process_command(self, command, *args):
        if command == 'SET':
            key, value = args
            self.data[key] = value
            print(f"Data set: {key} -> {self.data[key]}")  # Debugging statement
            return f'SET {key} {value}'
        elif command == 'GET':
            key = args[0]
            value = self.data.get(key, None)
            print(f"Data retrieved: {key} -> {value}")  # Debugging statement
            return value  # Return None if key not found
        elif command == 'DELETE':
            key = args[0]
            deleted = self.data.pop(key, None) is not None
            print(f"Data deleted: {key} -> {deleted}")  # Debugging statement
            return deleted  # Return True if deleted, else False
        elif command == 'HAS':
            key = args[0]
            return key in self.data
        elif command == 'CALL':
            method_name, method_args, method_kwargs = args
            return self.call_method(method_name, *method_args, **method_kwargs)
        elif command == 'REGISTER':
            method_name, method = args
            self.methods[method_name] = method
            return f'REGISTERED {method_name}'
        elif command == 'LIST_KEYS':
            return list(self.data.keys())
        elif command == 'LIST_DATA':
            return list(self.data.items())
        elif command == 'KILL':
            self.shutdown_server()
            return 'Server is shutting down...'
        else:
            return 'UNKNOWN_COMMAND'

    def call_method(self, method_name, *args, **kwargs):
        if method_name in self.methods:
            return self.methods[method_name](*args, **kwargs)
        else:
            return f"Method {method_name} not found."

    def start(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

    def shutdown_server(self):
        """
        Shutdown the server by closing the socket.
        """
        print("Shutting down the server...")
        self.server_socket.close()

    def print_data_periodically(self):
        while not self.stop_event.is_set():
            time.sleep(60)  # Sleep for one minute
            print("Current data:", self.data)

    def stop(self):
        self.stop_event.set()
        self.server_socket.close()

    @staticmethod
    def start_shared_manager(port_number=50000):
        def run_server():
            server = ProcessSharedObject(port=port_number)
            server.start()

        server_process = multiprocessing.Process(target=run_server)
        server_process.start()
        ProcessSharedObject.manager_process = server_process
        print(f"Server process started with PID: {server_process.pid}")
        return server_process

    @staticmethod
    def connect_to_shared_manager(port_number=50000):
        return SharedDataClient(port=port_number)

    @staticmethod
    def stop_shared_manager():
        if ProcessSharedObject.manager_process and ProcessSharedObject.manager_process.is_alive():
            print(f"Sending KILL command to server process with PID: {ProcessSharedObject.manager_process.pid}")
            client = SharedDataClient()
            client.send_command('KILL')
            ProcessSharedObject.manager_process.shutdown_server()
            try:
                ProcessSharedObject.manager_process.join(timeout=5)
                if ProcessSharedObject.manager_process.is_alive():
                    os.kill(ProcessSharedObject.manager_process.pid, 9)  # Force kill if not terminated
                    print(f"Force killed server process with PID: {ProcessSharedObject.manager_process.pid}")
            except Exception as e:
                print(f"Error during process join: {e}")
            print("Server process terminated.")
        ProcessSharedObject.manager_process = None

class SharedDataClient:
    def __init__(self, host='localhost', port=50000):
        self.host = host
        self.port = port

    def send_command(self, command, *args):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.host, self.port))
            client_socket.sendall(pickle.dumps((command, *args)))
            response = pickle.loads(client_socket.recv(4096))
            return response

    def set_data(self, key, value):
        return self.send_command('SET', key, value)

    def get_data(self, key):
        ret = self.send_command('GET', key)
        if ret == 'NOT_FOUND':
            return None
        return ret

    def has_data(self, key) -> bool:
        return self.send_command('HAS', key)

    def delete_data(self, key):
        ret = self.send_command('DELETE', key)
        if ret == 'NOT_FOUND':
            return None
        return ret

    def call_method(self, method_name, *args, **kwargs):
        return self.send_command('CALL', method_name, args, kwargs)

    def register_method(self, method_name, method):
        return self.send_command('REGISTER', method_name, method)

    def list_keys(self):
        return self.send_command('LIST_KEYS')

    def list_data(self):
        return self.send_command('LIST_DATA')

# Start Shared Manager and Register the stop_server_process function to be called on exit
ProcessSharedObject.start_shared_manager(50000)
atexit.register(ProcessSharedObject.stop_shared_manager)

class SharedProcessBase:
    """
    Base class for processes that interact with shared memory.

    Attributes:
        port_number (int): Port number for the shared manager server.
        shared_object: The shared object for inter-process communication.
    """
    def __init__(self, port_number=50000):
        self.port_number = port_number
        self.shared_object = None
        self.listeners = {}
        self.listener_thread = None
        # This is used to terminate listening threads when no longer needed
        self.stop_event = threading.Event()
        atexit.register(self.stop_listening)

    def register_method(self, method_name, method):
        """
        Registers methods that can be called remotely by other processes.

        Args:
            method_name (str): The name of the method to register.
            method: The method to register.
        """
        self.shared_object.register_method(method_name, method)

    def has_data(self, key) -> bool:
        """
        Checks if a key exists in shared memory.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return self.shared_object.has_data(key)

    def get_data(self, key):
        """
        Retrieves data from shared memory if it exists.

        Args:
            key (str): The key of the data to retrieve.

        Returns:
            The data associated with the key, or None if the key does not exist.
        """
        if self.shared_object.has_data(key):
            return self.shared_object.get_data(key)
        return None

    def list_data(self):
        """
        Lists all items in the shared memory.
        """
        return self.shared_object.list_data()

    def set_data(self, key, value):
        """
        Sets data in the shared memory.

        Args:
            key (str): The key of the data to set.
            value: The value to set.
        """
        self.shared_object.set_data(key, value)

    def delete_data(self, key):
        """
        Deletes data from the shared memory.

        Args:
            key (str): The key of the data to delete.
        """
        self.shared_object.delete_data(key)

    def call_remote_method(self, method_name, *args, **kwargs):
        """
        Calls a registered method on the shared object.

        Args:
            method_name (str): The name of the method to call.

        Raises:
            KeyError: If the method is not found.
        """
        if self.shared_object.has_data(method_name):
            self.shared_object.call_method(method_name, *args, **kwargs)
        else:
            raise KeyError(f"Method {method_name} not found in shared object.")

    def add_event_listener(self, event_name, callback):
        """
        Adds an event listener for the specified event.

        Args:
            event_name (str): The name of the event to listen for.
            callback (callable): The function to call when the event is fired.
        """
        if event_name in self.listeners:
            raise ValueError(f"Listener for event '{event_name}' already exists.")
        self.listeners[event_name] = callback

    def fire_event(self, event_name, value):
        existing_data = self.shared_object.get_data(event_name) or []
        if isinstance(existing_data, list):
            existing_data.append(value)
        else:
            existing_data = [existing_data, value]
        self.set_data(event_name, existing_data)

    def start_listening(self, asynchronous:bool):
        """
        Starts listening for events, either asynchronously or synchronously.
        Args:
            asynchronous (bool): If True, listens for events in a separate thread.
                                 If False, listens for events in the main thread.
        """
        self.stop_listening()  # Ensure any previous listener thread is stopped
        if asynchronous:
            self.listener_thread = threading.Thread(target=self._listen_for_events)
            self.listener_thread.daemon = True
            self.listener_thread.start()
        else:
            self._listen_for_events()

    def stop_listening(self):
        """
        Stops the listener thread.
        """
        self.stop_event.set()
        if self.listener_thread is not None and self.listener_thread != threading.current_thread():
            self.listener_thread.join()
            self.listener_thread = None
        self.stop_event.clear()

    def clear_listening(self):
        self.listeners.clear()

    def _listen_for_events(self):
        """
        The main loop for the listener thread.
        """
        while not self.stop_event.is_set():
            time.sleep(1)  # Polling interval
            for event_name, callback in self.listeners.items():
                if self.shared_object.has_data(event_name):
                    value = self.shared_object.get_data(event_name) or []
                    print("Listening for event:", event_name, "with value:", value)
                    self.shared_object.delete_data(event_name)  # Clear the event before handling
                    if isinstance(value, list):
                        for item in value:
                            try:
                                callback(item)
                            except Exception as e:
                                pass


    def connect_to_shared_memory(self, retries=5, delay=1):
        for attempt in range(retries):
            self.shared_object = ProcessSharedObject.connect_to_shared_manager(self.port_number)
            if self.shared_object:
                print("Connected to the shared manager server.")
                return
            print(f"Connection attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)



class ClientProcess(SharedProcessBase):
    """
    ClientProcess is a secondary process that interacts with shared memory and can call methods on ControllerProcess.

    Attributes:
        config: The configuration object passed from ControllerProcess.
    """
    def __init__(self, config, port_number = 50000):
        super().__init__(port_number)
        self.config = config  # Store the configuration
        self.connect_to_shared_memory()
        self.add_event_listener("terminate", self.on_terminate)
        self.add_event_listener("test_connection", self.on_test_connection)
        atexit.register(self.kill)

    def on_terminate(self, value):
        self.kill()

    def kill(self):
        print("Client: Terminate event received. Exiting process...")
        self.stop_listening()
        exit(0)

    def on_test_connection(self, value):
        print("Client: Received test connection request:", value)
        self.set_data("ack_connection", "pong")

    def run(self):
        """
        Main Method to run the ClientProcess
        """
        pass

    @classmethod
    def run_with_config(cls, config, port_number=50000):
        """
        Class method to instantiate ClientProcess with the given configuration.

        Args:
            config: The configuration object to pass to ClientProcess.
            port_number
        """
        client_process = cls(config, port_number)
        client_process.run()



class ControllerProcess(SharedProcessBase):
    """
    ControllerProcess is the primary process that manages shared memory and interacts with ClientProcess.

    Attributes:
        client_process_class: The class of the client process to be launched.
        client_process: The process instance for ClientProcess.
    """
    def __init__(self, client_process_class:ClientProcess, port_number=50000):
        super().__init__(port_number)
        self.client_process_class = client_process_class
        self.client_process = None
        atexit.register(self.cleanup)
        self.connect_to_shared_memory()

    def verify_connection(self, retries=6, delay=10):
        test_key = "test_connection"
        ack_key = "ack_connection"

        for _ in range(retries):
            self.set_data(test_key, "ping")
            time.sleep(delay)
            val = self.get_data(ack_key)
            if val == "pong":
                self.delete_data(ack_key)
                return True

        # If we reach here, it means the connection was not successful
        raise RuntimeError("ControllerProcess: Connection verification with client process failed.")
        self.terminate_client_process()


    def launch_client_process(self, config, force=True) -> bool:
        """
        Launches ClientProcess with configuration.

        Args:
            config: The configuration object to pass to ClientProcess.
        """
        if(not force and self.client_process is not None):
            return False
        if self.client_process is not None:
            self.terminate_client_process()  # Terminate existing client process if any
        self.client_process = Process(target=self.client_process_class.run_with_config, args=(config, self.port_number))
        self.client_process.start()

        # Verify connection to the shared manager
        if not self.verify_connection():
            print("ControllerProcess: Failed to connect to the shared manager after launching client process.")
            return False
        print("ControllerProcess: Client/Server Processes communication established.")
        return True

    def terminate_client_process(self):
        """
        Terminates the client process.
        """
        self.fire_event("terminate", True)
        time.sleep(1)
        if self.client_process is not None:
            print("Terminating ClientProcess...")
            try:
                self.client_process.terminate()
                self.client_process.join()
                print("ClientProcess terminated.")
            except Exception as e:
                pass
            finally:
                self.client_process = None

    def terminate_shared_manager(self):
        """
        Terminates the shared manager.
        """
        ProcessSharedObject.stop_shared_manager()

    def cleanup(self):
        self.terminate_client_process()
        self.terminate_shared_manager()

