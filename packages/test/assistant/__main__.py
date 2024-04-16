#--web true
#--kind python:default
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
import time

ROLE = """
You are a personal math tutor. Answer questions briefly.
"""

MODEL = "gpt-35-turbo"
#MODEL = "gpt-4"
AI = None
assistant = None
count = 0
thread = None

def req(msg):
    return [{"role": "system", "content": ROLE}, 
            {"role": "user", "content": msg}]

def ask(input):
    comp = AI.chat.completions.create(model=MODEL, messages=req(input))
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"

#create a Message on a Thread, then start (and return) a new Run
def submit_message(assistant, thread, user_message):
    AI.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return AI.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

#returns the last msg in a Thread
def get_response(thread):
    all_messages = AI.beta.threads.messages.list(
                thread_id=thread.id
            )
    return all_messages.data[0].content[0].text.value


# Waiting in a loop (with sleep)
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = AI.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(10)
    return run

def create_thread_and_run(assistant, user_input):
    thread = AI.beta.threads.create()
    run = submit_message(assistant, thread, user_input)
    return thread, run


def main(args):
    global AI, assistant, count, thread
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2024-02-15-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")
    if input == "":

        # Create and configure the assistant
        assistant = AI.beta.assistants.create(
            name="Math Tutor",
            instructions=ROLE,
            model=MODEL,
        )

        print('INFO: assistant created', assistant)
        print('INFO: assistant.id', assistant.id)

        return {
            "body": {
                "output": "Welcome to the OpenAI Assistant Test",
                "title": "OpenAI Math Tutor",
                "message": "You can ask for any mathematical operation"
            }
        }
    
    else:
        print("INFO count", count)
        print("INFO input", input)

        start = time.time()
        if(count == 0):
            thread, run = create_thread_and_run(assistant, input)
            count += 1
        else:
            run = submit_message(assistant, thread, input)

        wait_on_run(run, thread)

        output = get_response(thread)

        end = time.time()
        print("***CALL TIME", end - start)

        print("INFO response", output)

        return {
            "body": {
                "output":output,
            }
        }
