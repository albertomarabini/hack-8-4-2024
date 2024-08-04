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
#     example_controller.client_thread.list_data()  # same thing
#     example_controller.client_thread.call_method('custom_method')  # Simulate ClientProcess calling a custom method from the parent
#     example_controller.get_data('process_b_data')  # Example of deleting data from shared memory
#     example_controller.cleanup()  # Cleanup when needed


import time
import threading
from threading import Thread, Event
from multiprocessing.context import AuthenticationError
import time
import socket
# from shared_manager import start_shared_manager  # Import the shared manager function

# All Processes
from multiprocessing.managers import BaseManager


class ProcessShareManager(BaseManager):
    """
    Custom manager class that allows the sharing of complex objects
    between processes using the multiprocessing.managers.BaseManager.
    """
    pass

class ProcessSharedObject:
    """
    Manages shared data and methods between processes.

    Attributes:
        data (dict): A dictionary to store shared data.
        process_methods (dict): A dictionary to store registered methods
    """
    def __init__(self):
        self.data = {}
        self.methods = {}

    def set_data(self, key, value):
        self.data[key] = value

    def get_data(self, key):
        return self.data.get(key, None)

    def list_keys(self):
        return self.data.keys()

    def list_data(self):
        return self.data.items()

    def has_data(self, key) -> bool:
        return key in self.data

    def delete_data(self, key) -> bool:
        """
        Returns:
            bool: True if the key was deleted, False if the key was not found.
        """
        return self.data.pop(key, None) is not None

    def call_method(self, method_name, *args, **kwargs):
        """
        Calls a registered method
        """
        if method_name in self.methods:
            self.methods[method_name](*args, **kwargs)
        else:
            raise KeyError(f"Method {method_name} not found.")

    def register_method(self, method_name, method):
        self.methods[method_name] = method

    @staticmethod
    def start_shared_manager(port_number=50000, authkey=b'secret', stop_event=None):
        """
        Starts the shared manager server
        """
        shared_object = ProcessSharedObject()
        # Server-Side Registration of get_shared_object:
        ProcessShareManager.register('get_shared_object', callable=lambda: shared_object)

        manager = ProcessShareManager(address=('', port_number), authkey=b'secret')
    try:
        server = manager.get_server()
        print("Shared Manager Server running...")

        while not stop_event.is_set():
            try:
                conn = server.listener.accept()  # Accept a connection
                t = threading.Thread(target=server.handle_request, args=(conn,))
                t.daemon = True
                t.start()
            except OSError:
                continue
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print("Shared Manager Server is already running.")
        else:
            print(f"Server stopped with exception: {e}")
    except Exception as e:
        print(f"Server stopped with unexpected exception: {e}")
    finally:
        if 'server' in locals():
            server.listener.close()
        print("Shared Manager Server stopped.")


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



class ClientProcess(SharedProcessBase):
    """
    ClientProcess is a secondary process that interacts with shared memory and can call methods on ControllerProcess.

    Attributes:
        config: The configuration object passed from ControllerProcess.
    """
    def __init__(self, config, port_number = 50000):
        super().__init__(port_number)
        self.config = config  # Store the configuration
        self.stop_event = Event()
        self.connect_to_shared_memory()

    def connect_to_shared_memory(self):
        """
        Connects to the shared memory managed by the ProcessShareManager.
        """
        # Client-Side Registration of get_shared_object:
        ProcessShareManager.register('get_shared_object')
        manager = ProcessShareManager(address=('localhost', self.port_number), authkey=b'secret')
        manager.connect()
        self.shared_object = manager.get_shared_object()

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
        client_thread = cls(config, port_number)
        client_thread = Thread(target=client_thread.run)
        client_thread.start()
        return client_thread, client_thread.stop_event


class ControllerProcess(SharedProcessBase):
    """
    ControllerProcess is the primary process that manages shared memory and interacts with ClientProcess.

    Attributes:
        client_process_class: The class of the client process to be launched.
        manager_thread : The process instance for the shared manager.
        client_thread: The process instance for ClientProcess.
    """
    def __init__(self, client_process_class:ClientProcess, port_number=50000):
        super().__init__(port_number)
        self.client_process_class = client_process_class
        self.client_thread = None
        self.stop_event = None
        self.manager_thread  = None
        self.manager_stop_event = Event()
        self.start_or_connect_to_shared_manager()

    def start_or_connect_to_shared_manager(self, retry_count=0, max_retries=10):
        """
        Starts or connects to the shared manager server.

        Args:
            retry_count (int): The current number of connection attempts.
            max_retries (int): The maximum number of connection attempts allowed.
        """
        try:
            print(f"Attempting to register 'get_shared_object' with ProcessShareManager (retry {retry_count})")
            ProcessShareManager.register('get_shared_object')

            print(f"Creating manager with address ('localhost', {self.port_number}) and authkey=b'secret'")
            manager = ProcessShareManager(address=('localhost', self.port_number), authkey=b'secret')

            print("Attempting to connect to the manager server...")
            manager.connect()

            print("Successfully connected to the manager server. Retrieving shared object...")
            self.shared_object = manager.get_shared_object()
            print("Shared object successfully retrieved.")
        except (ConnectionRefusedError, socket.error, AuthenticationError, OSError) as e:
            if retry_count >= max_retries:
                print("Maximum retries reached. Could not connect to shared manager.")
                return
            print(f"Connection attempt {retry_count + 1} failed ({e}), starting shared manager server...")

            print("Starting shared manager server in a new thread...")
            self.manager_thread = Thread(target=ProcessSharedObject.start_shared_manager, args=(self.port_number, b'secret', self.manager_stop_event))
            self.manager_thread.start()

            print(f"Waiting for {2 * (retry_count + 1)} seconds before retrying...")
            time.sleep(2 * (retry_count + 1))  # Exponential backoff

            print(f"Retrying connection attempt {retry_count + 2}...")
            self.start_or_connect_to_shared_manager(retry_count + 1, max_retries)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


    def launch_client_process(self, config, force=True) -> bool:
        """
        Launches ClientProcess with configuration.

        Args:
            config: The configuration object to pass to ClientProcess.
        """
        if not force and self.client_thread is not None and self.client_thread.is_alive():
            return False
        self.terminate_client_process()  # Terminate existing client process if any
        self.client_thread, self.stop_event = self.client_process_class.run_with_config(config, self.port_number)
        return True

    def terminate_client_process(self):
        """
        Terminates the client process.
        """
        if self.client_thread is not None:
            print("Terminating ClientProcess...")
            self.manager_stop_event.set()
            self.manager_thread.join()
            print("ClientProcess terminated.")

    def terminate_shared_manager(self):
        """
        Terminates the shared manager.
        """
        if self.manager_thread  is not None:
            print("Terminating Shared Manager...")
            self.manager_thread .terminate()
            self.manager_thread .join()
            print("Shared Manager terminated.")

    def cleanup(self):
        self.terminate_client_process()
        self.terminate_shared_manager()
