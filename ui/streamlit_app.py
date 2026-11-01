"""Thin UI client; all retrieval and model logic lives behind FastAPI."""
import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
st.set_page_config(page_title='IronStore knowledge assistant', page_icon=':material/menu_book:', layout='centered')
st.session_state.setdefault('messages', [])


def api(method, path, **kwargs):
    try:
        response = httpx.request(method, API_URL + path, timeout=300, **kwargs)
        if response.is_error:
            detail = response.json().get('detail')
            message = detail if isinstance(detail, str) else 'Invalid request. Check file type, size and question length.'
            st.error(message)
            return None
        return response.json()
    except (httpx.HTTPError, ValueError):
        st.error('Cannot reach the API. Start FastAPI and check API_BASE_URL. A timed-out upload may still finish; retrying is safe.')
        return None


def show_response(result):
    st.markdown(result['answer'])
    if result.get('warning'):
        st.warning(result['warning'])
    if result.get('sources'):
        with st.expander('Source passages', expanded=False):
            for source in result['sources']:
                st.text(f"{source['document_name']} · page {source['page']}")
                st.caption(f"Chunk ID: {source['chunk_id']}")
                st.text(source['text'])
    if result.get('queries'):
        with st.expander('Retrieval details and comparison', expanded=False):
            st.text('Search queries:\n' + '\n'.join(result['queries']))
            comparison = result.get('comparison', {})
            standard = comparison.get('standard', [])
            multi = comparison.get('multi_query', [])
            st.caption(f'Standard: {len(standard)} chunks · Multi-query union: {len(multi)} chunks')
            rows = [{
                'Document': source['document_name'], 'Page': source['page'],
                'Standard': source['chunk_id'] in standard,
                'Multi-query': source['chunk_id'] in multi,
                'Chunk ID': source['chunk_id'],
            } for source in result.get('retrieved_sources', [])]
            if rows:
                st.dataframe(rows, hide_index=True, alt='Retrieved chunks and retrieval mode membership')
            st.caption('More retrieved passages do not necessarily mean a more accurate answer.')


with st.sidebar:
    st.title('IronStore')
    st.caption('Internal knowledge · Educational MVP')
    mode = st.segmented_control('Answer mode', ['standard', 'multi_query', 'agent'],
                               format_func=lambda x: {'standard': 'Standard', 'multi_query': 'Multi-query', 'agent': 'Agent'}[x],
                               default='standard', key='mode') or 'standard'
    st.caption('Agent can search, list documents, and summarize a selected document.')
    st.divider()
    st.subheader('Knowledge base')
    st.info('OpenAI processes uploaded document text for embeddings and answers. Upload only documents you are authorized to share.')
    files = st.file_uploader('Add company documents', type=['pdf', 'txt', 'md'], accept_multiple_files=True,
                             help='UTF-8 text or text PDFs. Maximum 10 MB per file. No scanned/encrypted PDFs.')
    if st.button('Index documents', disabled=not files, icon=':material/upload:', width='stretch'):
        with st.spinner('Extracting and indexing documents…'):
            for file in files:
                result = api('POST', '/documents/upload', files={'file': (file.name, file.getvalue(), file.type)})
                if result:
                    st.success(f"{file.name}: {'already indexed' if result['duplicate'] else 'indexed'} ({result['chunks']} chunks)")
    if st.button('Show indexed documents', icon=':material/folder_open:', width='stretch'):
        documents = api('GET', '/documents')
        if documents is not None:
            if documents:
                st.dataframe(documents, hide_index=True, alt='Names, IDs and chunk counts of indexed documents')
            else:
                st.caption('No documents indexed yet.')
    st.divider()
    if st.button('Clear chat', icon=':material/delete_sweep:', width='stretch'):
        st.session_state.messages = []
        st.rerun()
    st.caption('No authentication or access controls. Run locally with synthetic data.')

st.title('Your company knowledge, within reach')
st.caption('Ask a question. Check the evidence. Keep the conversation going.')
if not st.session_state.messages:
    with st.container(border=True):
        st.subheader('Start with a company procedure')
        st.markdown('Upload documents in the sidebar or index the included demo policies. Then try:\n\n'
                    '- How many days can I work remotely?\n- When should I submit an expense claim?\n'
                    '- What should I do if I lose my company laptop?')
        st.caption('Switch to Multi-query to compare retrieval, or Agent to list and summarize documents.')

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        if message['role'] == 'assistant':
            show_response(message['result'])
        else:
            st.markdown(message['content'])

if prompt := st.chat_input('Ask about your company documents', max_chars=2000, submit_mode='disable'):
    history = [{'role': m['role'], 'content': m['content'][:8000]} for m in st.session_state.messages[-20:]]
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.markdown(prompt)
    with st.chat_message('assistant'):
        with st.spinner('Finding evidence…'):
            result = api('POST', '/chat', json={'question': prompt, 'mode': mode, 'history': history})
        if result is not None:
            show_response(result)
            st.session_state.messages.append({'role': 'assistant', 'content': result['answer'], 'result': result})
