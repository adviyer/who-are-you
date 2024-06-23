import requests
import json
from dotenv import load_dotenv
import os
from groq import Groq
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/data', methods=['POST'])
def data_receiver():
    data = request.json  # Assuming JSON data
    # Here you can process your data or call another function
    response = process_data(data)
    return jsonify(response)

def process_data(data):
    # Your data processing logic here
    paper_name = data['paper_name']
    doi = data['doi']
    data_dict = find_papers(paper_name, doi)
    json_data = json.loads(json.dumps(data_dict))
    # print(json_data)
    json_data["hits"] = [hit for hit in json_data["hits"] if paper_name not in hit["title"]]
    print(json_data)
    output = {}
    output["hits"] = []
    filename = 'output.txt'

    for hit in json_data["hits"]:
        # if (check_snippet_valid(hit["snippets"]) == "yes" or check_snippet_valid(hit["description"]) == "yes") and check_link_valid(hit["url"]) == True:
        temp = {}
        temp["title"] = hit["title"]
        temp["url"] = hit["url"]
        temp["description"] = hit["description"]
        temp["snippets"] = hit["snippets"]
        output["hits"].append(temp)

    return {"status": "Processed", "data": output}

def get_ai_snippets_for_query(query):
    headers = {"X-API-Key": os.environ['YOU_API_KEY']}
    params = {"query": query}
    return requests.get(
        f"https://api.ydc-index.io/search",
        params=params,
        headers=headers,
    ).json()

def find_papers(name, doi, ):
    custom_prompt = "Find 5 DIFFERENT academic papers related to {} DOI:{}. also find something which is related to robotics".format(name, doi)
    return get_ai_snippets_for_query(custom_prompt)

def check_link_valid(url):
    research_sites = [
        "semanticscholar.org",
        "arxiv.org",
        "aclweb.org",
        "acm.org",
        "biorxiv.org"
    ]
    return any(site in url for site in research_sites)

def check_snippet_valid(snippet):
    client = Groq(
        api_key=os.getenv('GROQ_API_KEY'),
    )
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "you are a helpful assistant."
            },
            # Set a user message for the assistant to respond to.
            {
                "role": "user",
                "content": "If this summary is not empty, seems coherent, gramatically correct and sound like it's from the paper itself, say 'yes'. Otherwise, say 'no': {}".format(snippet)
            }
        ],

        model="llama3-8b-8192",
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stop=None,
        stream=False,
    )
    return str(chat_completion.choices[0].message.content)

if __name__ == '__main__':
    app.run(debug=True)
