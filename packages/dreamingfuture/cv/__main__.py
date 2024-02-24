#--web true
#--kind python:default
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
import re
import os
import chevron
import json
from bs4 import BeautifulSoup
import populate_cv




# ROLE = """
# You are DreamyBot, Assistant of Dreaming Future.
# DreamyBot is an intelligent chatbot designed to assist users in crafting professional resumes, 
# writing compelling cover letters, and preparing for successful job interviews. 
# As your virtual career advisor, Dreaming Future guides you through the process of 
# creating personalized documents tailored to your skills, experience, and career goals. 
# Whether you're a seasoned professional or a recent graduate, 
# Dreaming Future provides expert guidance and valuable insights to help you stand out in 
# today's competitive job market. 
# With its user-friendly interface and advanced AI capabilities, 
# Dreaming Future simplifies the job application process, e
# powering you to present yourself effectively and land your dream job.
# """

ROLE = """
Sei un assistente che chiede con gentilezza le informazioni di seguito descritte nel json, campo dati.
Se l'utente da solo il nome o solo il cognome, chiedi per l'altro campo, fin quando non ricevi tutti i campi che servono e che trovi nel json seguente:
- Name: nome e cognome
- Position: posizione lavorativa
- Contact phone: telefono 
- Contact email: indirizzo email
- Contact address: indirizzo 

Rispondi in json, di seguito rappresentato:
{
    text: "Grazie Mario Rossi per le informazioni fornite. Puoi vedere la nuova versione del tuo cv aggiornata qui a lato"
    data: {
        "name": "Mario Rossi",
        "position": "Marketing Manager",
        "contact": {
            "phone": "(+33) 777 777 77",
            "email": "lorem@ipsum.com",
            "address": "New York, USA",
        }
    }
}

Restituisci la sezione dati anche se hai ricevuto un solo campo.
"""

#MODEL = "gpt-35-turbo"
MODEL = "gpt-4"
AI = None
TEMPERATURE = .7
RESPONSE_FORMAT={ "type": "json_object" }
conversation=[{"role": "system", "content": ROLE}]
cv_template_path = "index.html"


# def req(msg):
#     return [{"role": "system", "content": ROLE}, 
#             {"role": "user", "content": msg}]

def ask(input):
    comp = AI.chat.completions.create(model=MODEL, 
                                    response_format=RESPONSE_FORMAT,
                                    messages=input, 
                                    temperature=TEMPERATURE)
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"


def extract(text):

    print("***RESPONSE:", text)

    json_object = json.loads(text)

    text = json_object.get("text", "")

    if 'data' in json_object:
        data = json_object['data']

        return {
            "text": text,
            "data": data
        }
    
    else:
        
        return {
            "text": text,
            "data": {}
        }



def render(src, args):
    with open(src) as f:
        return chevron.render(f, args)

def main(args):
    global AI
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")

    html_out = render(cv_template_path, args)

    if  input == "":
        return { 
            "body": {
            "output": "Benvenuto su SmartCV AI. Sono qui per aiutarti a compilare il tuo cv che vedi in preview. Per questo mi servono alcune informazioni, sei pronto?",
            "title": "SmartCV AI Chat",
            #"message": "You can chat with me to create your CV" #, cover letter or prepare for an interview"
            "html": html_out
            } 
        } 

    else:
        
        conversation.append({"role": "user", "content": input})
        
        res = ask(conversation)

        #print("res", res)
        output = extract(res)
        #trovre il modo di sintetizzare la conversazione con openai
        conversation.append({"role": "assistant", "content": res})

        if output["data"]:
            #Update CV
            print("***UPDATE CV***")
            populate_cv.update_cv(cv_template_path, output["data"])
            html_out = render(cv_template_path, args)
            return {
                "body": {
                    "output":output["text"],
                    "html": html_out
                }
            }

        return {
            "body": {
                "output":output["text"],
                #"html": html_out
            }
    }



