

from flask import Flask, render_template, send_from_directory, request, redirect
import json
from html import unescape
import requests

app = Flask(__name__)

HEADERS = {'Content-type': 'application/json'}
URL = "http://elasticsearch:9200/stackoverflow/_search?pretty=true&size=100"

def form_query(query):
    return json.dumps({
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": query,
                            "analyze_wildcard": True,
                            "time_zone": "Europe/Paris"
                        }
                    }
                ],
                "filter": [
                    {
                        "match_phrase": {
                            "PostTypeId": "1"
                        }
                    }
                ],
                "should": [],
                "must_not": []
            }
        }
    })



def question_query(id):
    return json.dumps({
        "query": {
            "bool": {
                "must": [
                    {
                        "match_all": {}
                    }
                ],
                "filter": [
                    {
                        "match_phrase": {
                            "Id": str(id)
                        }
                    }
                ],
                "should": [],
                "must_not": []
            }
        }
    })


def answers_query(id):
    return json.dumps({
        "query": {
            "bool": {
                "must": [
                    {
                        "match_all": {}
                    }
                ],
                "filter": [
                    {
                        "match_phrase": {
                            "ParentId": str(id)
                        }
                    }
                ],
                "should": [],
                "must_not": []
            }
        }
    })

@app.route('/', methods=["GET", "POST"])
def index():
    return redirect("search")



def extract(source):
    title = source.get("Title")
    if title:
        title = unescape(title)
    return dict(
        votes = source["Score"],
        id= source["Id"],
        answers= source.get("AnswerCount"),
        title=title,
        creation_date=source["CreationDate"][:10],
        tags=source.get("Tags"),
        body=source.get("Body")
    )

@app.route("/search")
def display_test_results():
    q = request.args.get("q")
    if not q:
        return render_template("recherche.html", questions=list(), searched="")
    query = form_query(q)
    h = requests.get(URL, headers=HEADERS, data=query).json()["hits"]["hits"]
    questions = [extract(r["_source"]) for r in h]
    return render_template("recherche.html", questions=sorted(questions, reverse=True, key=lambda x:x["votes"]), searched=q)


@app.route("/question/<int:id>")
def display_question(id):
    question = requests.get(URL, headers=HEADERS, data=question_query(id)).json()["hits"]["hits"][0]["_source"]
    answers = requests.get(URL, headers=HEADERS, data=answers_query(id)).json()["hits"]["hits"]
    answers = [x["_source"] for x in answers]
    print("Length of answers : {}".format(len(answers)))
    return render_template("base.html", question=extract(question), answers=sorted([extract(x) for x in answers], reverse=True, key=lambda x:x["votes"]))



@app.route('/static/<path:path>')
def serve_static(path):
    print("Hello")
    return send_from_directory(path)



app.run("0.0.0.0", "5000")
