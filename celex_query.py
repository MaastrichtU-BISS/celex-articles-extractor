import csv
import os
from pathlib import Path
from random import randint

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
limit_articles = 200
stop_execution = False
output_path = ""

with open('./input/data_10000.csv', mode='r') as f:
    results = []
    reader = csv.DictReader(f)
    row_count = 0
    for row in reader:
        row_count += 1
        if stop_execution:
            break
        print(parsed_documents, parsed_articles)
        try:
            builder = gs.Html2Json()
            url = build_url(row['celex'])
            doc = builder.convert_from_url(url)
            parsed_documents += 1
            articles = get_articles(doc['document'][2]['body'][0])
            print(f"Found {len(articles)} articles")
            if len(articles) > 9:
                temp_count = 0
                temp_article_count = 0
                while(temp_count == 0 and temp_article_count < len(articles)):
                    print("Randomly selecting article")
                    index = randint(0, len(articles) - 1)
                    filename_ = row['celex'] + "_Article_" + str(index + 1)
                    if os.path.exists(output_path.format(index + 1, filename_)):
                        temp_article_count += 1 
                        print("File already exists, trying again")
                        continue 
                    else:
                        print("Writing to file")
                        temp_count += 1
                        file = Path(
                            "./output/{}/{}.txt".format(index + 1, filename_))
                        file.parent.mkdir(parents=True, exist_ok=True)
                        temp_dict = articles[index]
                        file.write_text(temp_dict['full_text'])
                parsed_articles += 1
                if parsed_articles == limit_articles:
                    stop_execution = True
                    break
                '''
                for index, article in enumerate(articles):
                    filename_ = row['celex'] + "_Article_" + str(index + 1)
                    file = Path("./output/{}/{}.txt".format(index + 1, filename_)) 
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_text(article['full_text'])
                    parsed_articles += 1
                    if parsed_articles == limit_articles:
                        stop_execution = True
                        break
                '''
        except Exception:
            print(f"Failed to parse document: {row['celex']}")
            failed += 1
            continue 

print("Parsed Documents: {}, Failed: {}, Parsed Articles: {}".format(
    parsed_documents, failed, parsed_articles))
