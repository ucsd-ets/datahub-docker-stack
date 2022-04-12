import io
import yaml
import json
from os.path import join as pjoin
from os.path import isfile
from io import StringIO
import bitmath
from pandas import NaT, Series, read_csv, concat
from collections import deque
from typing import List,Dict

def get_specs(f_yaml:str)->Dict:
    """
    Parse specs from yaml file name to dict
    """
    with open(f_yaml, 'r') as f:
        specs = yaml.safe_load(f)
    return specs


def store_var(name:str, value:str, parent='artifacts')->None:
    '''
    Used to store the key value pair
    '''
    with open(pjoin(parent, name), 'w') as f:
        if isinstance(value, str):
            f.write(value)
        elif isinstance(value, list):
            for v in value:
                assert isinstance(v, str)
                f.write(v.strip() + '\n')
        else:
            raise NotImplementedError


def read_var(name:str, parent='artifacts')->str:
    '''
    Read the content from the file
    '''
    filepath = pjoin(parent, name)
    if isfile(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        if '\n' not in content:
            return content
        else:
            return content.split('\n')[:-1]
    else:
        return None


def store_dict(name:str, value:str, parent='artifacts')->None:
    '''
    Used to Dump the json file with the key value pair
    '''
    with open(pjoin(parent, name), 'w') as f:
        json.dump(value, f, indent=2)


def read_dict(name:str, parent='artifacts')->Dict:
    '''
    Read dict from the json file
    '''
    with open(pjoin(parent, name), 'r') as f:
        di = json.load(f)
    return di


def bytes_to_hstring(n_bytes:str):
    return (
        bitmath.Byte(int(n_bytes))
        .best_prefix(bitmath.SI)
        .format("{value:.1f} {unit}")
    )


def strfdelta(tdelta)->str:
    s = ""
    if tdelta is NaT:
        return s

    days = tdelta.days
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    if days:
        s = f"{days}d"
    if hours:
        s += f"{hours}h"
    if minutes:
        s += f"{minutes}m"

    return s + f"{seconds}s"


def json2series(jsobj, name:str=None, axis_name:str=None)->str:
    if isinstance(jsobj, dict):
        pass
    elif isinstance(jsobj, str) and isfile(jsobj):
        jsobj = json.load(open(jsobj))
    else:
        raise NotImplementedError

    srs = Series(jsobj, name=name)
    if axis_name:
        srs = srs.rename_axis(axis_name)
    return srs


def store_series(srs, path:str, parent:str='artifacts')->None:
    if parent:
        path = pjoin(parent, path)
    if not path.endswith('.csv'):
        path += '.csv'
    srs.to_csv(path)


def csv_embed_markdown(csv_path:str, markdown_path:str, title:str)->None:
    with open(csv_path, 'r') as f:
        csv = f.read()
    with open(markdown_path, 'w') as f:
        f.write(f"# {title}\n")
        f.write("```csv\n")
        f.write(csv)
        f.write("```\n")


def strip_csv_from_md(md_fp:str)->list:
    with open(md_fp, 'r') as f:
        doc = f.read()
        _, csv = doc.split('```csv\n')
        csv, _ = csv.split('\n```')
    return csv


def csv_to_pd(csv):
    fp_csv = StringIO(csv)
    return read_csv(fp_csv, index_col='image')


def csv_concat(csv_old:str, fp_new, out_fp)->None:
    fp_old = StringIO(csv_old)
    srs_old = read_csv(fp_old, index_col='image')
    srs_new = read_csv(fp_new, index_col='image')
    updated = concat([srs_new, srs_old])
    updated.to_csv(out_fp)


def insert_row(md_str:list, new_content:list)->str:
    lines = md_str.splitlines()
    table_i = [
        i for i, line in enumerate(lines)
        if line.strip() and line.strip()[0] == '|'
    ]
    header, content = lines[table_i[0]:table_i[0] +
                            2], lines[table_i[0]+2:table_i[-1]+1]

    n_columns = header[0].count('|') - 1
    print(n_columns)
    for line_tup in new_content:
        print(line_tup)
        assert len(line_tup) == n_columns
        assert all(isinstance(s, str) for s in line_tup)

    content = ['|'+'|'.join(line_tup) +
               '|' for line_tup in new_content] + content
    table_lines = header + content
    doc_lines = [line for i, line in enumerate(lines) if i not in table_i]
    doc_lines = doc_lines[:table_i[0]] + table_lines + doc_lines[table_i[0]:]
    doc = "\n".join(doc_lines)
    return doc



def list2cell(ls_str):
    return '<br>'.join(ls_str)


def url2mdlink(url, text):
    return f"[{text}]({url})"


def fulltag2fn(tag):
    return tag.replace('/', '-').replace(':', '-')


def get_prev_tag(img_name, tag_prefix=None):
    assert ':' not in img_name

    csv = strip_csv_from_md('wiki/Image Dependency.md')
    built_tags = csv_to_pd(csv).index

    if tag_prefix:
        filtered = built_tags[
            built_tags.str.contains(img_name) &
            built_tags.str.contains(tag_prefix)
        ]
    else:
        filtered = built_tags[built_tags.str.contains(img_name)]

    if len(filtered):
        return filtered[0]  # descending acc. date (latest is first)
    else:
        return None


def read_history():
    with open(pjoin('wiki', 'Home.md'), 'r') as f:
        doc_str = f.read()

    return doc_str


def query_images(history, commit_tag, keyword):
    images_in_row = [
        line.split('|')[2].replace('`', '').split('<br>')
        for line in 
        history.split('\n')
        if commit_tag in line
    ][0]

    filtered_images = list(filter(lambda img: keyword in img, images_in_row))
    assert len(filtered_images) != 0
    return filtered_images


def get_images_for_tag(history, commit_tag, keyword, tag_replace):
    original_names = query_images(history, commit_tag, keyword)
    new_names = [
        img[:img.index(':')+1] + tag_replace
        for img in original_names
    ]
    return dict(zip(original_names, new_names))

def subtree_order(image)->list:
    """pre-order DFS"""
    stack = deque()
    stack.append(image)
    order = []
    while stack:
        curr = stack.pop()
        order.append(curr)
        for child in curr.downstream:
            stack.append(child)
    return order

def get_level_order(image)->dict:
    '''BFS'''
   
    queue = [image]
    order = {}
    cnt = 0
    while queue:
        curr = queue.pop(0)
        for child in curr.downstream:
            queue.append(child)
        order[curr.image_name] =cnt
        cnt += 1
    return order