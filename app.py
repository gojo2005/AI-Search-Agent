import streamlit as st
import requests
import feedparser

from langchain.tools import Tool
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler

# Custom Wikipedia Tool 
def wiki_search(query: str):
    headers = {
        "User-Agent": "LangChainBot/1.0 (your_email@example.com)"
    }

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,
        "exintro": True,
        "redirects": 1,
        "titles": query,
    }

    try:
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params=params,
            headers=headers,
            timeout=10,
        )

        pages = response.json()["query"]["pages"]
        page = next(iter(pages.values()))

        return page.get("extract", "No Wikipedia article found.")

    except Exception as e:
        return f"Wikipedia Error: {e}"


wiki = Tool(
    name="Wikipedia",
    func=wiki_search,
    description="Use for general knowledge, definitions, history, people, anime, movies, places and companies."
)

#  Custom Arxiv Tool 
def arxiv_search(query: str):

    headers = {
        "User-Agent": "LangChainBot/1.0 (your_email@example.com)"
    }

    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query=all:{query.replace(' ','+')}"
        "&start=0&max_results=3"
    )

    try:
        response = requests.get(url, headers=headers, timeout=10)

        feed = feedparser.parse(response.text)

        if len(feed.entries) == 0:
            return "No papers found."

        output = ""

        for paper in feed.entries:

            output += f"""
Title: {paper.title}

Published: {paper.published}

Summary:
{paper.summary[:500]}

------------------------------------------------------------
"""

        return output

    except Exception as e:
        return f"Arxiv Error: {e}"


arxiv = Tool(
    name="Arxiv",
    func=arxiv_search,
    description="Use ONLY for research papers, scientific publications and academic literature."
)

# DuckDuckGo Search 
search = DuckDuckGoSearchRun(name="Search")

# Streamlit UI 
st.set_page_config(page_title="LangChain Search Agent", page_icon="🔎")

st.title("🔎 LangChain Search Agent")

st.write(
    """
This chatbot can answer questions using:

- 🌍 DuckDuckGo Search
- 📚 Wikipedia
- 📄 arXiv Research Papers
"""
)

# Sidebar  
st.sidebar.title("Settings")

api_key = st.sidebar.text_input(
    "Enter Groq API Key",
    type="password"
)

# Chat History 
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! Ask me anything."
        }
    ]

for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# User Input  
prompt = st.chat_input("Ask me anything...")

if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    st.chat_message("user").write(prompt)

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        streaming=True,
        temperature=0
    )

    tools = [
        search,
        wiki,
        arxiv
    ]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True
    )

    with st.chat_message("assistant"):

        st_cb = StreamlitCallbackHandler(
            st.container(),
            expand_new_thoughts=True
        )

        response = agent.run(
            prompt,
            callbacks=[st_cb]
        )

        st.write(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )