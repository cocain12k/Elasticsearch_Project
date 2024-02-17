from flask import Flask, request
from markupsafe import escape
from flask import render_template
from elasticsearch import Elasticsearch
import math

ELASTIC_PASSWORD = "INSERT PASSWORD HERE"

es = Elasticsearch("https://localhost:9200", http_auth=("elastic", ELASTIC_PASSWORD), verify_certs=False)
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    page_size = 1
    keyword = request.args.get('keyword')
    if request.args.get('page'):
        page_no = int(request.args.get('page'))
    else:
        page_no = 1
# rank by relavence score and the rating score
    body = {
        'size': page_size,
        'from': page_size * (page_no-1),
        'query': {
            'function_score': {
                'query': {
                    'multi_match': {
                        'query': keyword,
                        'fields': ['Name', 'Details (Comment/Desc)', 'Contacts (Tel_)', 'Location (Province)', 'Locaton (Add-ons)', 'Type (Food Specialty)'],
                        'fuzziness': 'AUTO'
                    }
                },
                'functions': [
                    {
                        'script_score': {
                            'script': {
                                'source': "doc['Ratings (Stars)'].value"
                            }
                        }
                    }
                ],
                'score_mode': 'multiply'
            }
        }

    }

    res = es.search(index='esan_res', body=body)
    hits = [{'name': doc['_source']['Name'], 'Details (Comment/Desc)': doc['_source']['Details (Comment/Desc)'], 'Locaton (Add-ons)': doc['_source']['Locaton (Add-ons)'],
             'tel': doc['_source']['Contacts (Tel_)'],'province': doc['_source']['Location (Province)'],'time': doc['_source']['Operation time'],
             'rating': doc['_source']['Ratings (Stars)'],'type': doc['_source']['Type (Food Specialty)']} for doc in res['hits']['hits']]
    page_total = math.ceil(res['hits']['total']['value']/page_size)
    return render_template('search.html',keyword=keyword, hits=hits, page_no=page_no, page_total=page_total)

if __name__ == '__main__':
    app.run(debug=True)
