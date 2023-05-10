# celex-articles-extractor
Scrapes eur-lex.europa.eu and parses the documents to segmentate them into articles.

# Input
In the input folder, place a csv file with at least one column called "celex".

# Execute
Run celex_query.py using Python3
 - Optional ( In the code of celex_query.py change the documents limmit or articles limit (default=90 articles) )

# Output
A folder called "output" will be created with subfolders called from 1 to k (k = maximun number of every article processed)
 - Example: a folder called 12 with 3 files inside, means that each one of those 3 files are the Article 12 of 3 different documents.

Inside each subfolder, multiple .txt files, named after their corresponding celex and containing the article's text.
