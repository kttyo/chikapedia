from django.shortcuts import render
from django.http import HttpResponse
import requests
import lxml.html
import CaboCha
import xmltodict
import random
import json
from os import path

if path.exists('/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd'):
    c = CaboCha.Parser('-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd')
elif path.exists('/usr/local/lib/mecab/dic/mecab-ipadic-neologd'):
    c = CaboCha.Parser('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')


def skip_brackets(text):
    """
    skip certain brackets and content within them
    """
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
    """
    split by '。', but do not split when within certain brackets
    """
    sentence_list = []

    brackets = {
        '「': '」',
        '『': '』',
    }
    bracket_end = None
    out_of_brackets = True

    sentence = ''
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
    if sentence != '\n':
        sentence_list.append(sentence)

    return sentence_list


def get_json_sentence(source_sentence):
    """
    turn a text into XML and then to JSON
    """
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


def random_img():
    if random.random() > 0.9:
        return 'https://images-na.ssl-images-amazon.com/images/I/51D021M66VL._SX338_BO1,204,203,200_.jpg'
    elif random.random() > 0.8:
        return 'https://s.yimg.jp/images/bookstore/ebook/web/content/image/etc/kaiji/itoukaiji.jpg'
    elif random.random() > 0.7:
        return 'https://s.yimg.jp/images/bookstore/ebook/web/content/image/etc/kaiji/ohtsuki.jpg'
    elif random.random() > 0.6:
        return 'https://s.yimg.jp/images/bookstore/ebook/web/content/image/etc/kaiji/hyoudoukazutaka.jpg'
    elif random.random() > 0.5:
        return 'https://s.yimg.jp/images/bookstore/ebook/web/content/image/etc/kaiji/endouyuji.jpg'
    elif random.random() > 0.4:
        return 'https://animemiru.jp/wp-content/uploads/2018/05/r-tonegawa01.jpg'
    elif random.random() > 0.3:
        return 'https://prtimes.jp/i/1719/1531/resize/d1719-1531-467330-0.jpg'
    elif random.random() > 0.2:
        return 'https://pbs.twimg.com/media/EOe8dtxU4AAiCzY.jpg'
    elif random.random() > 0.1:
        return 'https://livedoor.blogimg.jp/suko_ch-chansoku/imgs/4/1/417f3422-s.jpg'
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


def reference_update(elm, domain):
    element = elm
    if element.tag == 'link' and element.get('href'):
        if element.get('href')[0] == '/':
            element.set('href', 'https://ja.wikipedia.org' + str(element.get('href')))

    elif element.tag == 'a' and element.get('href'):
        if element.get('title'):
            element.attrib.pop('title')
        if element.get('href')[0] == '/':
            element.set('href', domain + '/wiki?url=https://ja.wikipedia.org' + str(element.get('href')))

    elif element.tag == 'img':
        if element.get('alt'):
            element.attrib.pop('alt')
        if element.get('title'):
            element.attrib.pop('title')
        if element.get('src')[0:8] == '/static/':
            element.set('src', 'https://ja.wikipedia.org' + str(element.get('src')))
        else:
            img_src = random_img()
            # img_src = '#'
            element.set('src', img_src)
            element.set('srcset', img_src)

    # print(len(element.getchildren()))
    if len(element.getchildren()) != 0:
        for child_element in element.getchildren():
            reference_update(child_element, domain)


def modify_element(elmt):
    """
    Receives HTML element and modifies it.
    """
    tag_map = []
    # keep replacement dictionary to revert the html tags after text conversion
    for i in elmt.getchildren():
        child_element = lxml.html.tostring(i, method='html', encoding="utf-8").decode()
        child_element = child_element[0:child_element.rfind('>') + 1]
        print(child_element)
        # tag_map[i.text_content()] = child_element
        if len(i.text_content()) > 0:
            tag_map.append({
                'before': i.text_content(),
                'after': child_element,
                'text_length': len(i.text_content())
            })

    # sort the dictionary by the length of keyword
    tag_map_sorted = sorted(tag_map, key=lambda i: i['text_length'])
    # print(json.dumps(tag_map_sorted, indent=2, ensure_ascii=False))

    # prepare texts
    print(elmt.text_content())
    mod_text = skip_brackets(elmt.text_content())
    print('mod_text ' + str(mod_text))
    sentence_list = split_sentence(mod_text)
    print(sentence_list)

    # run NLP and put together modified text
    modified_text = ''
    if len(sentence_list) > 0:
        for i in sentence_list:
            if i != '\n':
                json_text = get_json_sentence(i)
                if json_text['sentence']:
                    modified_text += get_updated_text(json_text)

    print('modified_text ' + str(modified_text))
    print(json.dumps(tag_map_sorted, indent=2, ensure_ascii=False))

    # add html tags back
    for i in range(len(tag_map_sorted)):
        modified_text = modified_text.replace(tag_map_sorted[i]['before'], tag_map_sorted[i]['after'])
    print(modified_text)
    print('--------------------------------------------------')

    for i in elmt.getchildren():
        elmt.remove(i)

    if modified_text:
        elmt.append(lxml.html.fromstring(modified_text))


def text_update(element):
    """
    Recursively look for certain html tags and pass it to modify_element function.
    """
    if element.tag == 'p':
        modify_element(element)
        # modify_element(element)
        # mod_text = skip_brackets(element.text_content())
        # sentence_list = split_sentence(mod_text)
        # print(sentence_list)


    elif len(element.getchildren()) != 0:
        for child_element in element.getchildren():
            text_update(child_element)


def wiki(request):
    """
    Take request, create html tree, and return as Httpresponse
    """
    domain = request._current_scheme_host

    if request.GET.get('url'):
        r = requests.get(request.GET.get('url'))

    elif request.GET.get('search'):  # check if URL contains parameter "search"
        r = requests.get('https://ja.wikipedia.org/w/index.php?search=' + str(
            request.GET.get('search')))

    else:
        r = requests.get('https://ja.wikipedia.org')

    # Start updating the HTML
    html_text = r.text
    html_text = html_text.replace('ウィキペディア', '地下ぺディア')
    html_tree = lxml.html.fromstring(html_text)

    reference_update(html_tree, domain)
    text_update(html_tree)

    if html_tree.cssselect('form'):
        for i in html_tree.cssselect('form'):
            if i.get('action'):
                i.set('action', domain + '/wiki')

    response_html = lxml.html.tostring(html_tree, method='html', encoding="utf-8").decode()

    return HttpResponse(response_html)  # directly returns http response
