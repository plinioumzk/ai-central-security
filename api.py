from flask import Flask, request, jsonify
from openai import OpenAI
from werkzeug.utils import secure_filename
import os
import time

def wait_on_run(run, thread_id, client):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run


app = Flask(__name__)

UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] =UPLOAD_FOLDER

client = OpenAI(
    # organization='org-11Qcu80v0wYOPv04D1cK73JA',
    api_key='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'
)

assistant_id = 'asst_ZuilBWsi6wqjafhhcFMrydpd'

def _create_thread():
    return client.beta.threads.create()

# openai.api_key = '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'
@app.route('/api/thread', methods=['POST'])
def create_thread():
    thread = _create_thread()
    return jsonify({'thread_id:': thread.id})


@app.route('/api/thread/<thread_id>/send_message', methods=['POST'])
def send_prompt(thread_id):

    # assistant = client.beta.assistants.create(
    #     name = "NewTranslator",
    #     instructions = "You are a translator. You will answer in spanish if user ask in portuguese or answer in french, if user ask in english",
    #     tools = [{"type": "code_interpreter"}],
    #     model = "gpt-4-1106-preview"
    # )

    # assistant_id = assistant.id

    if not request.is_json:
        return jsonify({"error": "Missing JSON in a request"}), 400

    data = request.get_json()
    prompt = data.get('prompt')

    # print(f"criou o assistant: {assistant_id}")

    my_assistant = client.beta.assistants.retrieve(assistant_id)
    print(my_assistant)

    print(f"Thread ID: {thread_id}")

    # Step 5: Add a Message to the Thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        # content=f"Which color is warm, red or blue?"
        content=prompt
    )
    print(f"Message: {message.content}")

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Retrieve the Assistant's Response
    run = wait_on_run(run, thread_id, client)

    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )

    response_messages = []

    print(f"Messages: {messages}")
    print(f"MessagesData: {messages.data}")
    # Print the Assistant's Response
    for message in reversed(messages.data):
        message_value = message.role + ": " + message.content[0].text.value
        response_messages.append(message_value)
    print(response_messages)

    # finalResponse = response.data['messages']

    # completion = client.chat.completions.create(
    # model="gpt-4-1106-preview",
    # messages=[
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Who won the 2018 World Cup!"}
    # ]
    # )

    # print(completion.choices[0].message)

    return jsonify({'response': response_messages[-1]})

@app.route('/api/file/analyze', methods=['POST'])
def analyze_file():
    if 'file' not in request.files:
        return 'No file part in request', 400
    file = request.files['file']

    if file.filename == '':
        return 'No selected file', 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    file_info=client.files.create(
        file=open(filename, 'rb'),
        purpose='assistants'
    )

    thread = _create_thread()

    message = client.beta.threads.messages.create(
        thread_id = thread.id,
        role = 'user',
        file_ids=[file_info.id],
        content='Explique o processo de alteração cadastral através do documento?'
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    run = wait_on_run(run, thread.id, client)

    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    response_messages = []

    for message in reversed(messages.data):
        message_value = message.role + ": " + message.content[0].text.value
        response_messages.append(message_value)

    print(response_messages)

    return jsonify({'response': response_messages[-1]})

if __name__ == '__main__':
    app.run(debug=True)


