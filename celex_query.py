import csv
from pathlib import Path

import get_structure as gs


def build_url(celex: str) -> str:
    return "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{}".format(
        celex)


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


parsed_documents = 0
failed = 0
parsed_articles = 0
limit_articles = 90
stop_execution = False

with open('./input/data.csv') as input:
    results = []
    reader = csv.DictReader(input)
    for row in reader:
        if stop_execution:
            break
        print(parsed_documents, parsed_articles)
        try:
            builder = gs.Html2Json()
            url = build_url(row['celex'])
            doc = builder.convert_from_url(url)
            parsed_documents += 1
            articles = get_articles(doc['document'][2]['body'][0])
            for index, article in enumerate(articles):
                file = Path(
                    "./output/{}/{}.txt".format(index + 1, row['celex']))
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(article['full_text'])
                parsed_articles += 1
                if parsed_articles == limit_articles:
                    stop_execution = True
                    break
        except Exception:
            print(f"Failed to parse document: {row['celex']}")
            failed += 1

print("Parsed Documents: {}, Failed: {}, Parsed Articles: {}".format(
    parsed_documents, failed, parsed_articles))
