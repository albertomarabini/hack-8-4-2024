from contextlib import contextmanager
import streamlit as st
import streamlit.components.v1 as components

class Modal:
    # Copyright (c) 2021, TeamTV
    # All rights reserved.

    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions are met:

    # 1. Redistributions of source code must retain the above copyright notice, this
    # list of conditions and the following disclaimer.

    # 2. Redistributions in binary form must reproduce the above copyright notice,
    # this list of conditions and the following disclaimer in the documentation
    # and/or other materials provided with the distribution.

    # 3. Neither the name of the copyright holder nor the names of its
    # contributors may be used to endorse or promote products derived from
    # this software without specific prior written permission.

    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    # AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    # IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    # DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    # FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    # DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    # SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    # CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    # OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

    def __init__(self, key, title=None, padding=20, max_width=744, has_close_button=True):
        """
        :param title: title of the Modal shown in the h1
        :param key: unique key identifying this modal instance
        :param padding: padding of the content within the modal
        :param max_width: maximum width this modal should use
        :param has_close_button: has a close button
        """
        self.title = title
        self.padding = padding
        self.max_width = str(max_width) + "px"
        self.key = key
        self.has_close_button = has_close_button

    def is_open(self):
        return st.session_state.get(f'{self.key}-opened', False)

    def open(self):
        st.session_state[f'{self.key}-opened'] = True
        st.rerun()

    def close(self, rerun_condition=True):
        print(st.session_state[f'{self.key}-opened'])
        st.session_state[f'{self.key}-opened'] = False
        if rerun_condition:
            st.rerun()

    @contextmanager
    def container(self):
        st.markdown(
            f"""
            <style>
            div[data-modal-container='true'][key='{self.key}'] {{
                position: fixed;
                width: 100vw !important;
                left: 0;
                z-index: 999992;
            }}

            div[data-modal-container='true'][key='{self.key}'] > div:first-child {{
                margin: auto;
            }}

            div[data-modal-container='true'][key='{self.key}'] h1 a {{
                display: none
            }}

            div[data-modal-container='true'][key='{self.key}']::before {{
                    position: fixed;
                    content: ' ';
                    left: 0;
                    right: 0;
                    top: 0;
                    bottom: 0;
                    z-index: 1000;
                    background-color: rgba(50,50,50,0.8);
            }}
            div[data-modal-container='true'][key='{self.key}'] > div:first-child {{
                max-width: {self.max_width};
            }}

            div[data-modal-container='true'][key='{self.key}'] > div:first-child > div:first-child {{
                width: unset !important;
                background-color: #fff; /* Will be overridden if possible */
                padding: {self.padding}px;
                margin-top: {2*self.padding}px;
                margin-left: -{self.padding}px;
                margin-right: -{self.padding}px;
                margin-bottom: -{2*self.padding}px;
                z-index: 1001;
                border-radius: 5px;
            }}
            div[data-modal-container='true'][key='{self.key}'] > div:first-child > div:first-child > div:first-child  {{
                overflow-y: scroll;
                max-height: 80vh;
                overflow-x: hidden;
                max-width: {self.max_width};
            }}

            div[data-modal-container='true'][key='{self.key}'] > div > div:nth-child(2)  {{
                z-index: 1003;
                position: absolute;
            }}
            div[data-modal-container='true'][key='{self.key}'] > div > div:nth-child(2) > div {{
                text-align: right;
                padding-right: {self.padding}px;
                max-width: {self.max_width};
            }}

            div[data-modal-container='true'][key='{self.key}'] > div > div:nth-child(2) > div > button {{
                right: 0;
                margin-top: {2*self.padding + 14}px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        with st.container():
            _container = st.container()
            if(self.has_close_button or self.title):
                title, close_button = _container.columns([1, 0.1])
                if self.title:
                    with title:
                        st.subheader(self.title)
                if self.has_close_button:
                    with close_button:
                        close_ = st.button('⠀✖⠀', key=f'{self.key}-close', type="primary")
                        if close_:
                            self.close()

        components.html(
            f"""
            <script>
            // STREAMLIT-MODAL-IFRAME-{self.key} <- Don't remove this comment. It's used to find our iframe
            const iframes = parent.document.body.getElementsByTagName('iframe');
            let container
            for(const iframe of iframes)
            {{
            if (iframe.srcdoc.indexOf("STREAMLIT-MODAL-IFRAME-{self.key}") !== -1) {{
                container = iframe.parentNode.previousSibling;
                container.setAttribute('data-modal-container', 'true');
                container.setAttribute('key', '{self.key}');

                // Copy background color from body
                const contentDiv = container.querySelector('div:first-child > div:first-child');
                contentDiv.style.backgroundColor = getComputedStyle(parent.document.body).backgroundColor;
            }}
            }}
            </script>
            """,
            height=0, width=0
        )

        with _container:
            yield _container


