# celex-articles-extractor
Scrapes eur-lex.europa.eu and parses the documents to segmentate them into articles.

# Input
In the input folder, place a csv file with at least one colummn called "celex".

# Execute
In the code set the documents or article limmit (default=90 articles)
Run celex_query.py using Python3

# Output
A folder called "output" will be created with subfolders called from 1 to k (k maximun number of every article processed)
Inside each subfolder a .txt file, named after their corresponding celex and containing the article text.
