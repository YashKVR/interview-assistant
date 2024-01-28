import openai
import os
from dotenv import find_dotenv, load_dotenv
import time
from datetime import datetime
import requests
import json
import streamlit as st
import tempfile

load_dotenv()

interviewer_assistant_id=os.environ.get("ASSISTANT_ID")

client = openai.OpenAI()

  
class AssistantManager:
    assistant_id = interviewer_assistant_id

    def __init__(self):
        self.client = client
        self.assistant = None
        self.thread = None
        self.run = None
        self.path = None
        self.file = None
        self.file_id = None
        self.job_role = None
        self.response = None

    def file_path(self):
        folder_path='.'
        filenames = os.listdir(folder_path)
        selected_filename = st.selectbox('Select a file', filenames)
        self.path = os.path.join(folder_path, selected_filename)
        


    def upload_file(self, path):
        # Upload a file with an "assistants" purpose
        file = client.files.create(file=open(path, "rb"), purpose="assistants")
        self.file = file
        self.file_id = file.id

    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
            print(f"Thread ID ==> {self.thread.id}") 

    def add_message_to_thread(self, role, content,file_id):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id = self.thread.id,
                role = role,
                content = content,
                file_ids= [file_id]
            )

    def run_assistant(self):
        if self.thread and self.assistant:
            run = self.client.beta.threads.runs.create(
                thread_id= self.thread.id,
                assistant_id= interviewer_assistant_id
            )
            self.run = run
            print(f"Run ===> {run}")

    def process_message(self):
        print("in process message")
        if self.thread:
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread.id
            )
            last_message = messages.data[0]
            role = last_message.role                                           
            response = last_message.content[0].text.value
            print(f"SUMMARY -----> {role.capitalize()} : =====> {response}")
            self.response = response

    def wait_for_completion(self):
        print("in wait")
        if self.thread and self.run:
            while True:
                print("True in wait")
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id = self.thread.id,
                    run_id = self.run.id
                )
                print(f"Run status ==> {run_status.model_dump_json(indent=4)}")

                if run_status.status == "completed":
                    self.process_message()                                           
        

def main():

    manager = AssistantManager()

    #streamlit intreface
    st.title("Ai Interviewer")
    manager.file_path()
    submit_button = st.button(label="Upload File")
    
    if submit_button:
        manager.upload_file(manager.path)
        print(f"File ===> {manager.file}")
        print(f"File ID ===> {manager.file.id}")
        if manager.file.id is not None:
            st.toast('File uploaded successfully', icon='😍')
            manager.create_thread()
        else:
            st.toast('File upload Failed', icon='😭')


    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)

        # Send message to openai
        manager.add_message_to_thread(
                  role="user",
                  content= prompt,
                  file_id=manager.file_id
              )
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        #Initiated Run
        manager.run_assistant()

        # Wait for completion and process the messages
        manager.wait_for_completion()

        response = f"{manager.response}"
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})                                    


if __name__ == "__main__":
    main()



       