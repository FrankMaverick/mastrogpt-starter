#--web true
import json

def main(arg):
    data = {
        "services": [
            # { 
            #     "name": "Demo", 
            #     "url": "mastrogpt/demo",
            # },
            # {
            #     "name": "OpenAI",
            #     "url": "openai/chat"
            # },
            { 
                "name": "SmartCV AI", 
                "url": "dreamingfuture/cv/template",
            },
        ]
    }
    return {"body": data}
