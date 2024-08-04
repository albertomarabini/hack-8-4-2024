import threading
import time
import requests
import os


class FlaskClient:
    def __init__(self, host=None, port=None, asynchronous=False):
        if host is None or port is None:
            host, port = self.get_host_port()
        self.base_url = f"http://{host}:{port}/command"
        self.listeners = {}
        self.listener_thread = None
        self.asynchronous = asynchronous
        self.is_listening = False
        self.lock = threading.Lock()

    #If i'm running in docker gets the configuration from the environment
    def get_host_port(self):
        def running_in_docker():
            path = '/proc/self/cgroup'
            return (
                os.path.exists('/.dockerenv') or
                os.path.isfile(path) and any('docker' in line for line in open(path))
            )

        if running_in_docker():
            host = os.getenv('FLASK_APP_HOST', 'flask-app')
            port = os.getenv('FLASK_APP_PORT', '5000')
        else:
            host = 'localhost'
            port = '5000'

        return host, port

    def _send_command(self, command, args=None):
        try:
            data = {'command': command, 'args': args or []}
            response = requests.post(self.base_url, json=data)
            response.raise_for_status()
            return response.json().get('result')
        except requests.RequestException as e:
            print(f"Error sending command {command}: {e}")
            return None

    def set_data(self, key, value):
        return self._send_command('SET', [key, value])

    def get_data(self, keys):
        if isinstance(keys, list):
            return self._send_command('GET', keys)
        else:
            return self._send_command('GET', [keys])

    def delete_data(self, key):
        return self._send_command('DELETE', [key]) == True

    def enqueue(self, key, value):
        current_data = self.get_data(key)
        if current_data is None:
            current_data = []
        elif not isinstance(current_data, list):
            current_data = [current_data]
        current_data.append(value)
        return self.set_data(key, current_data)

    def fire_event(self, key, value):
        return self.enqueue(key, value)

    def add_event_listener(self, event_name, callback):
        if event_name in self.listeners:
            raise ValueError(f"Listener for event '{event_name}' already exists.")
        self.listeners[event_name] = callback

    def start_listening(self):
        with self.lock:
            if not self.is_listening:
                self.is_listening = True
                if self.asynchronous:
                    if self.listener_thread is None:
                        self.listener_thread = threading.Thread(target=self._listen_for_events)
                        self.listener_thread.daemon = True
                        self.listener_thread.start()
                else:
                    self._listen_for_events()

    def stop_listening(self):
        with self.lock:
            self.is_listening = False
            if self.listener_thread is not None:
                self.listener_thread.join()
                self.listener_thread = None

    def listen_once(self, event_name: str | list | None=None, non_blocking=True):
        if event_name is None:
            event_names = list(self.listeners.keys())
        elif isinstance(event_name, list):
            event_names = event_name
        else:
            event_names = [event_name]

        while True:
            events_data = self.get_data(event_names)

            if events_data is None:
                if non_blocking:
                    return None
                else:
                    time.sleep(3)
                    continue

            with_listeners = {k: v for k, v in events_data.items() if k in self.listeners and v is not None}
            without_listeners = {k: v for k, v in events_data.items() if k not in self.listeners and v is not None}

            if with_listeners:
                self._process_events(with_listeners)

            if without_listeners:
                for event in without_listeners.keys():
                    self.delete_data(event)
                if len(without_listeners) == 1:
                    rv = next(iter(without_listeners.values())) #return just the first response
                    if isinstance(rv, list):
                        return rv[0]
                else:
                    return without_listeners #returns the dictionary of all the response

    def _listen_for_events(self):
        while self.is_listening:
            time.sleep(2)  # Polling interval
            event_names = list(self.listeners.keys())
            events_data = self.get_data(event_names)
            # events_data = {k: v for k, v in events_data.items() if v is not None}
            self._process_events(events_data)

    def _process_events(self, events_data):
        if events_data:
            for event_name, value in events_data.items():
                if value is not None:
                    print(f"Listening for event: {event_name} with value: {value}")
                    self.delete_data(event_name)  # Clear the event before handling
                    callback = self.listeners.get(event_name)
                    if callback:
                        if isinstance(value, list):
                            for item in value:
                                try:
                                    callback(item)
                                except Exception as e:
                                    print(f"Error handling callback for event '{event_name}': {e}")
                        else:
                            try:
                                callback(value)
                            except Exception as e:
                                print(f"Error handling callback for event '{event_name}': {e}")

    def has_data(self, key):
        return self._send_command('HAS', [key])

    def list_keys(self):
        return self._send_command('LIST_KEYS')

    def list_data(self):
        return self._send_command('LIST_DATA')

    def clear_data(self):
        return self._send_command('CLEAR') == "Data store cleared."

# Usage Example
if __name__ == '__main__':
    client = FlaskClient(asynchronous=True)

    def sample_callback(data):
        print(f"Event received: {data}")

    client.add_event_listener("test_event1", sample_callback)
    client.add_event_listener("test_event2", sample_callback)
    client.start_listening()

    # Simulate firing events
    client.fire_event("test_event1", {"message": "Hello, event1!"})
    client.fire_event("test_event2", {"message": "Hello, event2!"})
    time.sleep(5)  # Allow some time for the events to be processed

    client.stop_listening()

    # Test listen_once with blocking and non-blocking
    print(client.listen_once(non_blocking=True))  # Should return immediately
    print(client.listen_once(non_blocking=False))  # Should block until an event is received
