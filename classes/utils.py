import streamlit as st
import streamlit.components.v1 as components
import json
import uuid

# https://github.com/toolittlecakes/streamlit_js
# pip install streamlit-js
from streamlit_js import st_js, st_js_blocking

class stGetterSetter():
    def __init__(self, master_key):
        self.master_key = master_key

    def set(self, key, value):
        st.session_state[key + self.master_key] = value

    def get(self, key):
        if key + self.master_key not in st.session_state:
            return None
        return st.session_state[key + self.master_key]


class stFileManager:
    """ Initialize this class before to initialize other controls as it will authomatically load data in the state mgr"""
    def __init__(self, origin_dict):
        self.origin_dict = origin_dict
        if "filename" in self.origin_dict:
            self.load_file(self.origin_dict["filename"])
            self.origin_dict.pop("filename")

    def save_file(self, filename, keys):
        data_to_save = {key: self.origin_dict[key] for key in keys}

        # Write the dictionary to a file in JSON format
        with open(filename + ".cfg", 'w') as file:
            json.dump(data_to_save, file, indent=4)

    def page_rerun(self, filename):
        self.origin_dict["filename"] = filename
        st.rerun()

    # you can't call load_file directly as modifying the session_state
    # with the controls created would throw an error
    # so we need to rerun the page with the filename in the session_state
    # and then load the file
    def load_file(self, filename):
        # Open the file and load data into the dictionary
        try:
            with open(filename+ ".cfg", 'r') as file:
                data_loaded = json.load(file)
            for key, value in data_loaded.items():
                self.origin_dict[key] = value
        except FileNotFoundError:
            st.error(f"File {filename}.cfg not found.")

class stInjectCSS():
    def __init__(self, css_file:str):
        with open(css_file, "r") as f:
            css_content = f.read()
            css_escaped = css_content.replace("'", "\\'")
            javascript_code = f"""
                var style = window.parent.document.createElement('style');
                style.type = 'text/css';
                style.innerHTML = `{css_escaped}`;
                window.parent.document.head.appendChild(style);
            """
            st_js(code = javascript_code)

class stInjectFontAwesome():
    def __init(self):
            javascript_code = f"""
                var link = window.parent.document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css';
                window.parent.document.head.appendChild(link);
            """
            st_js(code = javascript_code)

class stClock:
    """_summary_
    This class creates a clock that will trigger a page rerun at a specified interval.
    (examin the possibility to have the btn rendered in a fragment)
    """
    def __init__(self, waiting_time, unique_key, debug=False):
        self.waiting_time = waiting_time
        self.unique_key = unique_key
        self.debug = debug

        if f'click_count_{self.unique_key}' not in st.session_state:
            st.session_state[f'click_count_{self.unique_key}'] = 0

        if f'tick_count_{self.unique_key}' not in st.session_state:
            st.session_state[f'tick_count_{self.unique_key}'] = 0

        if f'clock_running_{self.unique_key}' not in st.session_state:
            st.session_state[f'clock_running_{self.unique_key}'] = False

        # Define the button and update the session state
        if st.button(f"click command button ({self.unique_key})"):
            st.session_state[f'click_count_{self.unique_key}'] += 1
            st.session_state[f'tick_count_{self.unique_key}'] += 1

        self._inject_js()

    def _inject_js(self):

        debug_script = f"""
            console.log('Clock action: ' + action + ' | Click count: ' + {st.session_state[f'click_count_{self.unique_key}']} + ' | Tick count: ' + {st.session_state[f'tick_count_{self.unique_key}']});
        """ if self.debug else ""

        components.html(f"""
            <script>
            let clockInterval;

            window.parent.find_clock_button = function() {{
                // Find the button by its inner text in the parent document
                let buttons = Array.from(this.document.getElementsByTagName('button'));
                let targetButton = buttons.find(el => el.innerText === 'click command button ({self.unique_key})');
                return targetButton;
            }}

            window.parent.triggerButtonClick = function() {{
                let targetButton = this.find_clock_button();
                if (targetButton) {{
                    targetButton.click();
                }}
            }}

            window.parent.startClock = function(running) {{
                let action = (!running)?'start':'running';
                {debug_script}
                this.stopClock(true);  // Ensure any existing interval is cleared
                this.clockInterval = this.setInterval(this.triggerButtonClick, {self.waiting_time * 1000});
            }}

            window.parent.stopClock = function(stop_log) {{
                let action = 'stop';
                if (!stop_log) {{
                    {debug_script}
                }}
                this.clearInterval(this.clockInterval);
            }}

            window.parent.rerunPage = function() {{
                let action = 'rerun';
                {debug_script}
                this.triggerButtonClick();
            }}

            // Restore clock state on reload
            if ({'true' if st.session_state[f'clock_running_{self.unique_key}'] else 'false'}) {{
                window.parent.startClock(true);
            }}
            window.parent.setTimeout("window.parent.find_clock_button().parentElement.parentElement.style.display = 'none';", 0);
            </script>
            """, height=0)

    def start(self, immediate=False):
        st.session_state[f'clock_running_{self.unique_key}'] = True
        if immediate:
            self.rerun_page()
        components.html('<script>window.parent.startClock();</script>', height=0)

    def stop(self, immediate=False):
        st.session_state[f'clock_running_{self.unique_key}'] = False
        if immediate:
            self.rerun_page()
        else:
            components.html('<script>window.parent.stopClock();</script>', height=0)

    def rerun_page(self):
        components.html('<script>window.parent.rerunPage();</script>', height=0)

    def get_click_count(self):
        return st.session_state[f'click_count_{self.unique_key}']

    def get_tick_count(self):
        return st.session_state[f'tick_count_{self.unique_key}']

# Example usage
# # Instantiate and use the Clock class
# clock = stClock(waiting_time=5, unique_key="unique1", debug=True)  # Initialize with a 5 second interval

# # Control buttons for the clock
# if st.button("Start Clock"):
#     clock.start()

# if st.button("Stop Clock"):
#     clock.stop()

# if st.button("Rerun Now"):
#     clock.rerun_page()

# st.button("Regular Rerun")

# # Display the click count and tick count
# st.write(f"Button clicked {clock.get_click_count()} times!")
# st.write(f"Page rerun {clock.get_tick_count()} times!")

class stChat(stGetterSetter):
    def __init__(self, key, parent_component=None, height=None):
        super().__init__(key)
        self.key = key
        self.parent_component = parent_component or st
        self.column = self.parent_component.container(height = height)  # Create a column within the parent component
        self._init_session_state()
        self._render()

    def _init_session_state(self):
        if self.get('messages') is None:
            self.set('messages', [])
        if self.get('input_required') is None:
            self.set('input_required', False)
        if self.get('prompt') is None:
            self.set('prompt', "")
        if self.get('callback') is None:
            self.set('callback', None)
        if self.get('user_input') is None:
            self.set('user_input', "")

    def add_message(self, role, message, rerun=True):
        messages = self.get('messages')
        messages.append({"role": role, "message": message})
        self.set('messages', messages)
        if rerun:
            st.rerun()

    def get_input(self, prompt, role, callback):
        self.add_message(role, prompt, rerun=False)
        self.set('input_required', True)
        self.set('prompt', prompt)
        self.set('callback', callback)
        st.rerun()

    def _handle_send_click(self):
        self.set('input_required', False)
        user_input = self.get('user_input')
        self.add_message("user", user_input, rerun=False)
        callback = self.get('callback')
        if callback:
            self.set('callback', None)
            callback(user_input)
        # No rerun here

    def _render(self):
        # self.column.title("Chat Interface")
        messages = self.get('messages')
        for msg in messages:
            if msg["role"] == "user":
                self.column.write(f"**User:** {msg['message']}")
            else:
                self.column.write(f"**{msg['role'].capitalize()}:** {msg['message']}")

        if self.get('input_required'):
            self.set('user_input', self.column.text_input("Please enter your input:", key=f'{self.key}_chat_input'))
            self.column.button("Send", on_click=self._handle_send_click)

    def reset(self):
        self.set('messages', [])
        self.column.empty()


