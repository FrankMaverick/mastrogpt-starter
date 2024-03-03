#--web true
import json

def main(arg):
    data = {
        "services": [
            # { 
            #     "name": "Demo", 
            #     "url": "mastrogpt/demo",
            # },
            {
                "name": "OpenAI",
                "url": "openai/chat"
            },
            { 
                "name": "SmartCV AI (COM)", 
                "url": "dreamingfuture/cvcompletion",
            },
            { 
                "name": "SmartCV AI (ASS)", 
                "url": "dreamingfuture/cvassistant",
            },
        ]
    }
    return {"body": data}
