from django.shortcuts import render
from django.http import HttpResponse
import requests
import lxml.html
import CaboCha
import xmltodict
import random


#domain = 'http://127.0.0.1:8000'
domain = 'http://chikapedia.meatthezoo.org'

#c = CaboCha.Parser('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')
c = CaboCha.Parser()


def skip_brackets(text):
    # skip certain brackets and content within them
    brackets = {
        '[': ']',
        '(': ')',
        '（': '）',
    }
    bracket_end = None
    reading = True
    p_modified = ''

    for letter in text:
        if reading:
            if letter in brackets.keys():
                reading = False
                bracket_end = brackets[letter]
            else:
                p_modified += letter
        else:
            if letter == bracket_end:
                reading = True
                bracket_end = None
    return p_modified


def split_sentence(p):
    # split by '。', but do not split when within certain brackets
    sentence_list = []
    sentence = ''
    brackets = {
        '「': '」',
        '『': '』',
    }
    bracket_end = None

    out_of_brackets = True

    for letter in p:
        if out_of_brackets:
            if letter in brackets.keys():
                out_of_brackets = False
                bracket_end = brackets[letter]
                sentence += letter
            elif letter == '。':
                # sentence += letter
                sentence_list.append(sentence)
                sentence = ''
            else:
                sentence += letter
        else:
            if letter == bracket_end:
                sentence += letter
                out_of_brackets = True
            else:
                sentence += letter

    return sentence_list


def get_json_sentence(source_sentence):
    # turn a text into XML and then to JSON
    tree = c.parse(source_sentence)
    xmltree = tree.toString(CaboCha.FORMAT_XML)
    jsonobj = xmltodict.parse(xmltree, attr_prefix='', cdata_key='surface', dict_constructor=dict)
    json_sentence = {
        'sentence': jsonobj['sentence'],
        'original_text': source_sentence
    }

    # turn all chunk lists into list
    if json_sentence['sentence']:
        if type(json_sentence['sentence']['chunk']) is not list:
            json_sentence['sentence']['chunk'] = [json_sentence['sentence']['chunk']]
        # turn all tok lists into list
        for chunk in json_sentence['sentence']['chunk']:
            if type(chunk['tok']) is not list:
                chunk['tok'] = [chunk['tok']]
            # turn all feature lists into list
            for tok in chunk['tok']:
                feature_list = tok['feature'].split(',')
                tok['feature'] = feature_list

    return json_sentence


def random_text():
    if random.random() > 0.9:
        return '悪魔的'
    elif random.random() > 0.8:
        return '悪魔的'
    elif random.random() > 0.7:
        return 'キンキンに冷えた'
    else:
        return ''


def get_updated_text(json_element):
    returned_text = ''
    for i in json_element['sentence']['chunk']:
        for j in i['tok']:
            if 'surface' in j.keys():
                if j['feature'][0] == '名詞' and j['feature'][1] == '一般':
                    returned_text += random_text()
                    returned_text += j['surface']
                elif j['feature'][0] == '名詞' and j['feature'][1] == 'サ変接続':
                    returned_text += '圧倒的'
                    returned_text += j['surface']
                else:
                    returned_text += j['surface']
        returned_text += '...'
    returned_text += '！'
    return returned_text


def reference_update(element):
    if element.tag == 'link' and element.get('href'):
        if element.get('href')[0] == '/':
            element.set('href', 'https://ja.wikipedia.org' + str(element.get('href')))

    if element.tag == 'a' and element.get('href'):
        if element.get('href')[0] == '/':
            element.set('href', domain + '/wiki?url=https://ja.wikipedia.org' + str(element.get('href')))

    if element.tag == 'img' and element.get('src'):
        if element.get('src')[0:8] == '/static/':
            element.set('src', 'https://ja.wikipedia.org' + str(element.get('src')))

    elif len(element.getchildren()) != 0:
        for child_element in element.getchildren():
            reference_update(child_element)


def text_update(element):
    if element.tag == 'p' or element.tag == 'li':

        mod_text = skip_brackets(element.text_content())
        sentence_list = split_sentence(mod_text)

        updated_text = ''
        for i in sentence_list:
            json_text = get_json_sentence(i)
            if json_text['sentence']:
                updated_text += get_updated_text(json_text)
                element.text = updated_text

    elif len(element.getchildren()) != 0:
        for child_element in element.getchildren():
            text_update(child_element)


def wiki(request):
    if request.GET.get('url'):
        r = requests.get(request.GET.get('url'))

    elif request.GET.get('search'):
        r = requests.get(domain + '/wiki?url=https://ja.wikipedia.org/w/index.php?search=' + str(
            request.GET.get('search')))

    else:
        r = requests.get(domain + '/wiki?url=https://ja.wikipedia.org')

    htmltree = lxml.html.fromstring(r.text)

    reference_update(htmltree)
    text_update(htmltree)

    if htmltree.cssselect('form'):
        for i in htmltree.cssselect('form'):
            if i.get('action'):
                i.set('action', domain + '/wiki')

    response_html = lxml.html.tostring(htmltree, method='html', encoding="utf-8").decode()

    return HttpResponse(response_html)  # directly returns http response
