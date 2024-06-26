from bs4 import BeautifulSoup
import re
import json
import random
import requests
from http.server import BaseHTTPRequestHandler


class ReChecker:

    def __init__(self) -> None:
        self.translations = {
            "part": ["part", "deel"],
            "title": ["title", "titel"],
            "chapter": ["chapter", "hoofdstuk"],
            "section": ["section", "afdeling"],
            "subsection": ["subsection", "subafdeling"],
            "article": ["article", "artikel"]
        }

    def check_fragment_type(self, s: str, name: str) -> bool:
        for w in self.translations[name]:
            if len(re.findall("^\n*{}\s\w+\n*$".format(w), s.lower())):
                return True
        return False

    def start_with_number_and_point(self, s):
        return re.findall('^\d+\.', s)

    def start_with_number_and_parenthesis(self, s):
        return re.findall('^\(?\d+\)', s)

    def start_with_letter_parenthesis(self, s):
        return re.findall('^\(?[a-z]{1}\)', s)

    def start_with_roman_number_parenthesis(self, s):
        return re.findall('^\(?[ivxcl—]+\)?', s)


class ReCleaner:
    def merge_lines(self, match_obj):
        if match_obj.group() is not None:
            return re.sub(r'(\n+)$', '\t', match_obj.group())

    def remove_new_lines(self, s):
        return re.sub(r'\n+', '', s)

    def trim_new_lines(self, s):
        trimmed = re.sub(r'\n+', '\n\n', s)
        trimmed = re.sub(r'\n+(\(?\w+\)|\—|\w+\.)\n+',
                         self.merge_lines, trimmed)
        c = 0
        for i in range(len(trimmed)):
            if trimmed[i] == '\n':
                c += 1
            else:
                break
        return trimmed[c:]


class Html2Json:
    def __init__(self) -> None:
        self.re_checker = ReChecker()
        self.re_cleaner = ReCleaner()

    def convert_from_url(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return self.convert(response.text)

    def get_field(self, s):
        if self.oj_format:
            return 'oj-' + s
        return s

    def go_back_untill_same_level(self, stack, level, res):
        self.add_to_dic(stack, res, 0)
        while stack[-1][0] >= level:
            stack.pop()

    def add_to_dic(self, stack, current, i):
        if i >= len(stack):
            return
        p_key = stack[i][1]["parent_key"]
        name = stack[i][1]["name"]
        text = stack[i][1]["text"]
        if not p_key in current:
            current[p_key] = [{"name": name, "text": text}]
        else:
            for el in current[p_key]:
                if el["name"] == name:
                    self.add_to_dic(stack, el, i + 1)
                    return
            current[p_key].append({"name": name, "text": text})
        self.add_to_dic(stack, current[p_key][-1], i + 1)

    def get_introduction(self, soup, stack, res):
        current = soup.find(attrs={"class": "doc-ti"})
        if current == None:
            self.oj_format = True
            current = soup.find(attrs={"class": "oj-doc-ti"})
        while current != None:
            try:
                if current.name != 'p':
                    break
            except:
                pass
            s = self.re_cleaner.trim_new_lines(current.get_text())
            self.get_paragraphs(s, stack, res)
            current = current.find_next_sibling()
        self.go_back_untill_same_level(stack, 1, res)
        return current

    def get_recitals(self, current, stack, res):
        while current != None:
            try:
                if current.name != 'table':
                    if not (current.name == 'p' and self.get_field('normal') in current['class']):
                        break
            except:
                pass
            s = self.re_cleaner.trim_new_lines(current.get_text())
            self.get_paragraphs(s, stack, res)
            current = current.find_next_sibling()
        self.go_back_untill_same_level(stack, 1, res)

    def get_body(self, soup, stack, res):
        ti_secs = soup.find_all(
            attrs={"class": self.get_field("ti-section-1")})
        if len(ti_secs) == 0:
            self.get_articles(soup.find(
                attrs={"class": self.get_field("ti-art")}), stack, res)
        else:
            for ti in ti_secs:
                s = self.re_cleaner.remove_new_lines(ti.get_text())
                if self.re_checker.check_fragment_type(s, "part"):
                    if stack[-1][0] >= 1:
                        self.go_back_untill_same_level(stack, 1, res)
                    stack.append(
                        (1, {"parent_key": "parts", "name": s, "text": self.re_cleaner.remove_new_lines(ti.find_next_sibling().get_text())}))
                elif self.re_checker.check_fragment_type(s, "title"):
                    if stack[-1][0] >= 2:
                        self.go_back_untill_same_level(stack, 2, res)
                    stack.append(
                        (2, {"parent_key": "titles", "name": s, "text": self.re_cleaner.remove_new_lines(ti.find_next_sibling().get_text())}))
                elif self.re_checker.check_fragment_type(s, "chapter"):
                    if stack[-1][0] >= 3:
                        self.go_back_untill_same_level(stack, 3, res)
                    stack.append(
                        (3, {"parent_key": "chapters", "name": s, "text": self.re_cleaner.remove_new_lines(ti.find_next_sibling().get_text())}))
                elif self.re_checker.check_fragment_type(s, "section"):
                    if stack[-1][0] >= 4:
                        self.go_back_untill_same_level(stack, 4, res)
                    stack.append(
                        (4, {"parent_key": "sections", "name": s, "text": self.re_cleaner.remove_new_lines(ti.find_next_sibling().get_text())}))
                elif self.re_checker.check_fragment_type(s, "subsection"):
                    if stack[-1][0] >= 5:
                        self.go_back_untill_same_level(stack, 5, res)
                    stack.append(
                        (5, {"parent_key": "subsections", "name": s, "text": self.re_cleaner.remove_new_lines(ti.find_next_sibling().get_text())}))
                else:
                    pass
                try:
                    potential_art = ti.find_next_sibling().find_next_sibling()
                    if self.get_field('ti-art') in potential_art['class']:
                        self.get_articles(potential_art, stack, res)
                    else:
                        potential_art = potential_art.find(
                            attrs={'class': self.get_field('ti-art')})
                        if potential_art != None:
                            self.get_articles(potential_art, stack, res)
                except:
                    potential_art = potential_art.find(
                        attrs={'class': self.get_field('ti-art')})
                    if potential_art != None:
                        self.get_articles(potential_art, stack, res)
        self.go_back_untill_same_level(stack, 1, res)

    def get_notes(self, soup, stack, res):
        current = soup.find(
            'hr', attrs={"class": self.get_field("note")}).find_next_sibling()
        while current != None:
            try:
                if self.get_field('doc-sep') in current['class'] or self.get_field('doc-end') in current['class']:
                    break
            except:
                pass
            s = self.re_cleaner.trim_new_lines(current.get_text())
            self.get_paragraphs(s, stack, res)
            current = current.find_next_sibling()
        self.go_back_untill_same_level(stack, 1, res)

    def get_annexes(self, soup, stack, res):
        docseps = soup.find_all(attrs={'class': self.get_field('doc-sep')})
        self.total_annexes = len(docseps)
        for sep in docseps:
            ti = sep.find_next_sibling().find(
                attrs={"class": self.get_field("doc-ti")})
            s = self.re_cleaner.trim_new_lines(
                ti.get_text())
            stack.append((6, {"parent_key": "annex", "name": s,
                         "text": ti.find_next_sibling().get_text()}))

            current = ti.find_next_sibling().find_next_sibling()
            while current != None:
                try:
                    if self.get_field('final') in current['class'] or self.get_field('doc-sep') in current['class']:
                        break
                except:
                    pass
                s = self.re_cleaner.trim_new_lines(current.get_text())
                self.get_paragraphs(s, stack, res)
                current = current.find_next_sibling()
            self.go_back_untill_same_level(stack, 1, res)

        self.go_back_untill_same_level(stack, 1, res)

    def get_articles(self, art, stack, res):
        current = art
        while current != None:
            try:
                if self.get_field('final') in current['class'] or self.get_field('ti-section-1') in current['class']:
                    break
            except:
                pass

            s = self.re_cleaner.trim_new_lines(current.get_text())

            if self.re_checker.check_fragment_type(s, "article"):
                if stack[-1][0] >= 6:
                    self.go_back_untill_same_level(stack, 6, res)
                stack.append((6, {"parent_key": "articles", "name": s,
                             "text": self.re_cleaner.remove_new_lines(current.find_next_sibling().get_text())}))
                current = current.find_next_sibling()
            else:
                self.get_paragraphs(s, stack, res)

            if current.find_next_sibling() == None:
                potential_art = None
                if current.parent.find_next_sibling() != None:
                    potential_art = current.parent.find_next_sibling().find(
                        attrs={'class': self.get_field('ti-art')})
                if potential_art != None:
                    current = potential_art
                else:
                    break
            else:
                current = current.find_next_sibling()

    def get_paragraphs(self, s, stack, res):
        match_num = self.re_checker.start_with_number_and_point(s)
        match_num_par = self.re_checker.start_with_number_and_parenthesis(s)
        match_lett = self.re_checker.start_with_letter_parenthesis(s)
        if len(match_num) == 1:
            if stack[-1][0] >= 7:
                self.go_back_untill_same_level(stack, 7, res)
            stack.append(
                (7, {"parent_key": "paragraphs", "name": match_num[0], "text": s}))
        elif len(s) > 0 and s[-1] == ':':
            if stack[-1][0] >= 7:
                self.go_back_untill_same_level(stack, 7, res)
            stack.append(
                (7, {"parent_key": "paragraphs", "name": ":", "text": s}))
        elif len(match_lett) == 1:
            if stack[-1][0] >= 8:
                self.go_back_untill_same_level(stack, 8, res)
            children = s.split('\n\n')
            stack.append(
                (8, {"parent_key": "paragraphs", "name": match_lett[0], "text": children[0]}))
            # check if roman numbers
            if len(children) > 2:
                for roman in children[1:len(children)-1]:
                    match_roman = self.re_checker.start_with_roman_number_parenthesis(
                        roman)
                    if len(match_roman) == 1:
                        if match_roman[0] == '—':
                            if stack[-1][0] >= 10:
                                self.go_back_untill_same_level(
                                    stack, 10, res)
                            stack.append(
                                (10, {"parent_key": "paragraphs", "name": match_roman[0] + str(random.randrange(10000)), "text": roman}))
                        else:
                            if stack[-1][0] >= 9:
                                self.go_back_untill_same_level(
                                    stack, 9, res)
                            stack.append(
                                (9, {"parent_key": "paragraphs", "name": match_roman[0], "text": roman}))
        elif len(match_num_par) == 1:
            if stack[-1][0] >= 8:
                self.go_back_untill_same_level(stack, 8, res)
            stack.append(
                (8, {"parent_key": "paragraphs", "name": match_num_par[0], "text": s}))
        elif len(s) > 0 and s[0] == "—":
            if stack[-1][0] >= 8:
                self.go_back_untill_same_level(stack, 8, res)
            stack.append(
                (8, {"parent_key": "paragraphs", "name": "—_" + str(random.randrange(10000)), "text": s}))
        else:
            if stack[-1][0] >= 7:
                self.go_back_untill_same_level(stack, 7, res)
            stack.append(
                (7, {"parent_key": "paragraphs", "name": "text_" + str(random.randrange(10000)), "text": s}))

    def convert(self, text: str) -> dict:
        res = {"document": [{}, {}, {}, {}, {}]}
        soup = BeautifulSoup(text, 'html.parser')
        self.oj_format = False
        current = self.get_introduction(soup, [(
            0, {"parent_key": "introduction", "name": "introduction", "text": "introduction"})], res["document"][0])
        self.get_recitals(current, [
            (0, {"parent_key": "recitals", "name": "recitals", "text": "recitals"})], res["document"][1])
        self.get_body(soup, [
                      (0, {"parent_key": "body", "name": "body", "text": "body"})], res["document"][2])
        self.get_notes(soup, [
                      (0, {"parent_key": "notes", "name": "notes", "text": "notes"})], res["document"][3])
        self.get_annexes(soup, [
            (0, {"parent_key": "annexes", "name": "annexes", "text": "annexes"})], res["document"][4])

        self.add_full_text_to_articles(res["document"][2], False)
        return res

    def add_full_text_to_articles(self, current, inside_art) -> str:
        full_text = []
        for key in current:
            if isinstance(current[key], list):
                for el in current[key]:
                    full_text.append(el["text"])
                    if key == "articles":
                        full_text += self.add_full_text_to_articles(
                            el, True)
                        el["full_text"] = '\n\n'.join(full_text)
                        full_text = []
                    else:
                        full_text += self.add_full_text_to_articles(
                            el, inside_art)
        return full_text


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        content_len = int(self.headers.get('content-length', 0))
        url = self.rfile.read(content_len).decode()
        builder = Html2Json()
        res = builder.convert_from_url(url)
        self.wfile.write(json.dumps(res).encode())
        return
