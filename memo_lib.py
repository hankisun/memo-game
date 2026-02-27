from loguru import logger
import re
import json

# Logger configuration is handled by the main application (memo_streamlit.py).

def new_tab_dict(title=""):
    return {
        "title": title,
        "columns": [],
        "contents": [],
        "before_sep_bar": True
    }

def check_doc_title(l):
    if m := re.search(r"^#+\s*(.+)", l):
        return m.groups()[0]
    return None

def parse_table_row(l):
    if m := re.findall(r"\|([^\|]+)", l):
        return m
    return None

def check_table_column(l, tab_dict):
    if tab_dict["before_sep_bar"] is False:
        return None
    return parse_table_row(l)  

def is_seperation_bar(l):
    if m := re.search(r"^\|(?:\s*\:?-+\:?\s*\|)+", l):
        logger.debug(f"{m.span()} {len(l)}")
        if m.span()[1] == len(l):
            return True
    return False

def is_md_table(l):
    if m := re.search(r"^\|", l):
        return True
    return False

def insert_to_tab_dict(l, tab_dict):
    if is_seperation_bar(l):
        tab_dict["before_sep_bar"] = False
    elif columns := check_table_column(l, tab_dict):
        logger.debug(columns)
        tab_dict['columns'] = [column.strip() for column in columns]
    else: # contents
        parsed = parse_table_row(l)
        tab_dict['contents'].append({column: content.strip() for (column, content) in zip(tab_dict['columns'], parsed)})

def read_md(path):
    docs = []
    tab_dict = new_tab_dict()
    
    with open(path) as f:
        while True:
            l = f.readline()
            if not l:
                break
            l = l.strip()
            if title := check_doc_title(l):
                if tab_dict["contents"]:
                    docs.append(tab_dict)
                tab_dict = new_tab_dict(title)
            elif is_md_table(l):
                insert_to_tab_dict(l, tab_dict)

    logger.debug(json.dumps(docs, ensure_ascii=False, indent=2))
    logger.info(f"{len(docs)} tables are loaded")
    return docs
