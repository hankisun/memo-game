import streamlit as st
import os
import sys
import re
import random
import git
import json
from pathlib import Path
from collections import defaultdict
from loguru import logger
from memo_lib import read_md

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}", level="INFO")

st.set_page_config(page_title="Memorization Practice", layout="centered")
st.title("Memorization Practice")
CONFIG_PATH = Path.cwd() / 'settings.json'


def load_config():
    try:
        if CONFIG_PATH.exists():
            cfg = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            logger.info(f"load config : {cfg}")
            return cfg
    except Exception:
        pass
    return {}

def set_session_state_with_config(cfg):
    st.session_state.settings_repo_url = cfg.get('repo_url', '')
    st.session_state.settings_repo_name = ''
    if repo_url := st.session_state.settings_repo_url:
        if matched:= re.findall(r'/([\w\-\.]+)\.git$', repo_url):
            st.session_state.settings_repo_name = matched[0]
    st.session_state.settings_query_columns = split_cols(cfg.get('query_columns', ''))
    st.session_state.settings_answer_columns = split_cols(cfg.get('answer_columns', ''))


def save_config(cfg: dict):
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        logger.error(f'Failed to save config: {e}')

def load_md_files():
    dir_path = os.path.join(os.getcwd(), st.session_state.settings_repo_name)

    # Get all md files in the directory
    md_files = [f for f in os.listdir(dir_path) if f.endswith(('.md', '.markdown'))]
    if len(md_files) == 0:
        st.error('No md files exist')
        st.stop()
    st.session_state.md_files = md_files
    st.session_state.dir_path = dir_path

def clone_repo(cfg: dict):
    repo_url = cfg.get('repo_url', '')
    if not repo_url:
        st.error('Repo url is not set. Please go settings first')
        st.stop()
    try:
        git.Repo.clone_from(repo_url, st.session_state.settings_repo_name)
        logger.info("cloned")
    except git.exc.GitCommandError  as e:
        logger.error(f"cloned failure {e.stderr}")
        st.error('Git clone error')
        st.stop()
    except Exception as e:
        logger.error(f"Unexpected Error {e}")
        st.error('Unexpected Error while cloning')
        st.stop()
    
def pull_repo():
    try:
        res = git.Repo(st.session_state.settings_repo_name).git.pull()
        logger.info(f"pulled  memorization repo : {res}")
    except git.exc.GitCommandError  as e:
        st.error('Git pull error')
        st.stop()
    except Exception as e:
        logger.error('Unexpected Error while pulling')
        st.stop()
    
def init_state():
    if 'md_files' not in st.session_state:
        st.session_state.md_files = []
    if 'docs' not in st.session_state:
        st.session_state.docs = []
    if 'contents' not in st.session_state:
        st.session_state.contents = []
    if 'selected_table' not in st.session_state:
        st.session_state.selected_table = None
    if 'idx' not in st.session_state:
        st.session_state.idx = 0
    if 'correct' not in st.session_state:
        st.session_state.correct = 0
    if 'incorrect' not in st.session_state:
        st.session_state.incorrect = 0
    if 'incorrect_counts' not in st.session_state:
        st.session_state.incorrect_counts = []
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    if 'dir_path' not in st.session_state:
        st.session_state.dir_path = None
    if 'settings_repo_url' not in st.session_state:
        st.session_state.settings_repo_url = ''
    if 'settings_repo_name' not in st.session_state:
        st.session_state.settings_repo_name = ''
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    

def update_selected_md():
    selected_md = st.session_state.selected_md

    try:
        file_path = os.path.join(st.session_state.dir_path, selected_md)
        docs = read_md(file_path)
        logger.info(f"loaded {selected_md}")
    except Exception as e:
        st.error(f'Failed to read file: {e}')
        docs = []

    if docs:
        st.session_state.docs = docs

def update_selected_table():
    selected = st.session_state.selected_table
    if selected == 'Test All':
        contents = [c for tab in st.session_state.docs for c in tab.get('contents', [])]
    else:
        for tab in st.session_state.docs:
            if tab['title'] == selected:
                contents = tab.get('contents', [])
                break

    if contents:
        logger.info(f"selected table : {selected}")
        random.shuffle(contents)
        st.session_state.contents = contents
        st.session_state.idx = 0
        st.session_state.correct = 0
        st.session_state.incorrect = 0
        st.session_state.incorrect_counts = [0 for _ in range(len(contents))]
        st.session_state.show_answer = False
    else:
        logger.warning(f"Empty contents in table : {selected}")

def reorder_contents():
    contents = st.session_state.contents
    return [c for _, c in sorted(zip(st.session_state.incorrect_counts, contents), key=lambda x: x[0], reverse=True)]

def get_column_list(docs):
    col_cnt = defaultdict(int)
    for doc in docs:
        for col in doc["columns"]:
            col_cnt[col] += 1

    cols = sorted(col_cnt.items(), key=lambda x: x[1], reverse=True)
    return [col for col, cnt in cols]
    # return [f"{col} ({cnt})" for col, cnt in cols]

def get_default_col_idx(col_list, default_cols):
    for i, col in enumerate(col_list):
        if col in default_cols:
            return i
    return None

def split_cols(s):
    ret = []
    for col in re.split("[,;]", s):
        if c := col.strip():
            ret.append(c)
    return ret

@st.dialog("Settings")
def open_settings():
    logger.info("OPen Settings")
    cfg = load_config()
    repo_url = st.text_input('Repo Url', value=cfg.get('repo_url', ''))
    qc = st.text_input('Query columns', 
                       value=cfg.get('query_columns', ''),
                       placeholder='comma seperated list')
    ac = st.text_input('Answer columns', 
                       value=cfg.get('answer_columns', ''),
                       placeholder='comma seperated list')
    c1, c2, _ = st.columns([2, 2, 6])
    if c1.button('Save', width="stretch"):
        set_session_state_with_config(cfg)
        save_config({'repo_url': repo_url, 'query_columns': qc, 'answer_columns': ac})
        st.success('Settings saved')
        st.session_state.initialized = False
        st.rerun()
    if c2.button('Cancel', width="stretch"):
        st.rerun()

init_state()
if st.session_state.initialized == False:
    if cfg := load_config():
        set_session_state_with_config(cfg)
    else:
        st.warning("Configure Settings please")

    if not os.path.isdir(st.session_state.settings_repo_name):
        clone_repo(cfg)
    
    load_md_files()
    st.session_state.initialized = True

with st.sidebar:
    # Header with Settings button
    cols = st.columns([2.8, 1, 1])
    with cols[0]:
        st.header('Load Questions')
    with cols[1]:
        if st.button('🔃', key='reload_repo', help='Reload repo'):
            pull_repo()
    with cols[2]:
        if st.button('⚙️', key='open_settings', help='Settings'):
            open_settings()

    if md_files := st.session_state.md_files:
        # Step 2: Select markdown file
        selected_file = st.selectbox(
            'Select markdown file:', 
            md_files,
            index=None,
            key='selected_md',
            on_change=update_selected_md)

    # Load the file and get table list
    if docs := st.session_state.docs:
        column_list = get_column_list(docs)
        # preselect from saved settings if available (case-sensitive)
        sel_q = st.session_state.get('settings_query_columns', [])
        sel_a = st.session_state.get('settings_answer_columns', [])
        q_idx = get_default_col_idx(column_list, sel_q)
        a_idx = get_default_col_idx(column_list, sel_a)

        st.selectbox(
            'Query column',
            column_list,
            index=q_idx,
            key='selected_query_column',
        )
        st.selectbox(
            'Answer column',
            column_list,
            index=a_idx,
            key='selected_answer_column',
        )
        st.header('Select a Table')
        
        # Step 3: Select table from the markdown file
        table_options = ['Test All'] + [tab['title'] for tab in docs]
        
        selected_table = st.radio(
            'Choose table:',
            table_options,
            index=None,
            key='selected_table',
            on_change=update_selected_table
        )
    else:
        st.warning('No tables found in the file')


if not st.session_state.contents:
    st.info('Please upload a markdown file or enter a path in the sidebar to begin.')
    st.stop()

contents = st.session_state.contents
idx = st.session_state.idx
item = contents[idx]
query_col = st.session_state.selected_query_column
answer_col = st.session_state.selected_answer_column
# logger.info(f"q: {query_col} a: {answer_col}")

st.subheader(f'Question {idx+1} / {len(contents)}')
st.write(f"**{query_col}:** {item.get(query_col, '')}")

with st.form(f'answer_form_{idx}'):
    user_answer = st.text_input('Write the answer')
    submitted = st.form_submit_button('Check')

if submitted:
    correct_answer = item.get(answer_col, '')
    if user_answer.strip() == correct_answer:
        st.success('Correct!')
        st.session_state.correct += 1
    else:
        st.error('Incorrect..')
        st.session_state.incorrect += 1
        st.session_state.incorrect_counts[idx] += 1
    st.session_state.show_answer = True

st.write(f"(Correct {st.session_state.correct} / Incorrect {st.session_state.incorrect})")
if st.session_state.correct == len(contents):
    st.header("Perfect!")
if st.session_state.show_answer:
    st.write(f"**{answer_col}:** {item.get(answer_col, '')}")
    if st.button('Next', key=f'next_{idx}'):
        next_idx = (st.session_state.idx + 1) % len(contents)
        if next_idx == 0:
            st.session_state.contents = reorder_contents()
            st.session_state.correct = 0
            st.session_state.incorrect = 0
        st.session_state.idx = next_idx
        st.session_state.show_answer = False
        st.rerun()
