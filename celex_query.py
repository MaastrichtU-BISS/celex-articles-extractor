import csv
import json
import get_structure as gs


def build_url(celex: str) -> str:
    return "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{}".format(celex)


def get_articles(body: dict) -> str:
    if 'articles' in body:
        return body['articles']
    else:
        results = []
        for key in body:
            if key != 'name' and key != 'text':
                for child in body[key]:
                    results += get_articles(child)
        return results


parsed = 0
failed = 0
with open('./input/data.csv') as input:
    results = []
    reader = csv.DictReader(input)
    for row in reader:
        try:
            builder = gs.Html2Json()
            url = build_url(row['celex'])
            doc = builder.convert_from_url(url)
            articles = get_articles(doc['document'][2]['body'][0])
            for index, article in enumerate(articles):
                with open("./output/{}_{}".format(row['celex'], index + 1), "w+") as output:
                    output.write(json.dumps(article))
                    parsed += 1
        except:
            failed += 1

print("Parsed: {}, Failed: {}".format(parsed, failed))
