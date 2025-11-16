from google import genai
from google.genai.types import GenerateContentConfig
from google.genai.types import Tool
from bs4 import BeautifulSoup
import os
import requests
import datetime

#WEBSCRAPING
def scrapeLink(link):
    response = requests.get(link)
    html_content = BeautifulSoup(response.text, 'html.parser')
    return html_content

def soupFind(html_content,tag,target):
    soupmix = list()
    for content in html_content.find_all(tag):
        try:
            if target == "text":
                soupmix.append(content.get_text())
            else:
                soupmix.append(content.get(target))
        except Exception as e:
            print(f"Error occurred: {e}")
    return soupmix

#TWO STEP GEMINI CALL (URL CONTEXT + STRUCTURED OUTPUT)
def scaleGemini_v1(request,url):
    client = genai.Client(api_key = os.getenv("GEMINI_API_KEY"))

    prompt = request

    if len(url) > 0:

        try:
            prompt = "Retrieve as much relevant, accurate, and unbiased information as possible from the provided references."
            prompt += f" References: "
            for link in url.split(" "):
                prompt += link + ", "

            tools = [
                {"url_context": {}},
            ]

            response = client.models.generate_content(
                model = "gemini-2.5-flash-lite", contents = prompt, 
                config = GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=1000,
                    tools = tools
                ),
            )

            return request + " Web context: " + response.text

        except Exception as e:
            print(f"Error occurred: {e}")

    else:

        schema = {
            "type": "object",
            "properties":{
                "analysis": {"type": "string", "description": "detailed analysis of stock"},
                "function": {"type": "string", "description": "best course of action to take, according to analysis", "enum": ["buy","sell","hold"]},
                "weight": {"type": "number", "description": "confidence weight of function from 0 to 1, with 0 = definitive sell, 0.5 = hold, 1 = definitive buy"}
            },
            "required": ["analysis", "function", "weight"]
        }

        response = client.models.generate_content(
            model = "gemini-2.5-flash-lite", contents = prompt, 
            config = GenerateContentConfig(
                temperature=0,
                max_output_tokens=1000,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        
    return response.text

#SINGLE STEP GEMINI CALL (URL CONTEXT INPUT + STRUCTURED OUTPUT))
def scaleGemini_v2(request,url):

    client = genai.Client(api_key = os.getenv("GEMINI_API_KEY"))
    
    prompt = request

    for link in url.split(" "):
        prompt += "*** START OF SITE ***" + scrapeLink(link).get_text() + "*** END OF SITE ***"

    schema = {
        "type": "object",
        "properties":{
            "analysis": {"type": "string", "description": "detailed analysis of stock"},
            "function": {"type": "string", "description": "best course of action to take, according to analysis", "enum": ["buy","sell","hold"]},
            "weight": {"type": "number", "description": "confidence weight of function from 0 to 1, with 0 = definitive sell, 0.5 = hold, 1 = definitive buy"}
        },
        "required": ["analysis", "function", "weight"]
    }

    response = client.models.generate_content(
        model = "gemini-2.5-flash-lite", contents = prompt, 
        config = GenerateContentConfig(
            temperature=0,
            max_output_tokens=1000,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )

    return response.text    

#LOG DATA
def log(fileName,data):
    timeStamp = datetime.datetime.now()
    with open(fileName,"a") as file:
        file.write(f"{timeStamp}\n" + f" {data}\n")

def read(fileName):
    with open(fileName,"r") as file:
        for line in file:
            print(line)

#print(scrapeLink("https://www.google.com/finance/quote/AAPL:NASDAQ?sa=X&ved=2ahUKEwint9u7yfGQAxWvr1YBHUAuFIYQ3ecFegQINBAb").get_text())
#print(scaleGemini_v1(scaleGemini_v1("Fetch current data of this stock.","https://www.google.com/finance/quote/DJT:NASDAQ?sa=X&ved=2ahUKEwjO1prplvSQAxViZvUHHRzEC-QQ3ecFegQIUBAb"),""))
#print(scaleGemini_v2("Fetch current data of this stock.","https://www.google.com/finance/quote/DJT:NASDAQ?sa=X&ved=2ahUKEwjO1prplvSQAxViZvUHHRzEC-QQ3ecFegQIUBAb"))

datav1 = scaleGemini_v1(scaleGemini_v1("Fetch current data of this stock.","https://www.google.com/finance/quote/DJT:NASDAQ?sa=X&ved=2ahUKEwjO1prplvSQAxViZvUHHRzEC-QQ3ecFegQIUBAb"),"")
datav2 = scaleGemini_v2("Fetch current data of this stock.","https://www.google.com/finance/quote/DJT:NASDAQ?sa=X&ved=2ahUKEwjO1prplvSQAxViZvUHHRzEC-QQ3ecFegQIUBAb")
log("testlog.txt",datav2)
print(datav2)
print(datav1)