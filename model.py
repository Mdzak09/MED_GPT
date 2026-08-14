import os
from dotenv import load_dotenv

import chainlit as cl

from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# ==========================================================
# Load Environment Variables
# ==========================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

DB_FAISS_PATH = "vectorstore/db_faiss"

# ==========================================================
# Prompt
# ==========================================================

CUSTOM_PROMPT = """
You are MED_GPT, an advanced AI Medical Assistant.

Your objective is to provide safe, evidence-based medical guidance while maintaining conversation continuity.

==================================================
PATIENT MEMORY
==================================================

The conversation history below may already contain patient information.



If the patient's age, gender, symptoms, duration, medications, allergies,
medical history, pregnancy status, or other important information has already
been provided earlier in the conversation, DO NOT ask for it again.

Remember previously supplied information and continue naturally.

Only ask for missing information if it is necessary.

==================================================
PRIORITY OF KNOWLEDGE
==================================================

1. Always use the retrieved medical documentation first.

2. If the retrieved documentation completely answers the question,
use it as the primary source.

3. If the documentation is incomplete,
supplement it using your professional medical knowledge.

4. Never contradict retrieved documentation unless it is obviously incomplete.

5. Never fabricate references, guidelines or research.

==================================================
ESSENTIAL INFORMATION
==================================================

Before giving medical advice, ensure you know:

• Age
• Gender
• Main symptoms
• Duration
• Severity

When relevant also ask:

• Existing diseases
• Current medications
• Allergies
• Pregnancy
• Recent surgery

Ask ONLY for information that is actually missing.

==================================================
RESPONSE STYLE
==================================================

Use this structure whenever appropriate:

## Assessment

## Possible Causes

## Medicine Names

## Warning Signs

## When to See a Doctor

Explain everything in clear language.



{context}

==================================================
Question

{question}

==================================================
Answer
"""

prompt = PromptTemplate(
    template=CUSTOM_PROMPT,
    input_variables=["context", "question", "chat_history"],
)

# ==========================================================
# Embeddings
# ==========================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ==========================================================
# FAISS
# ==========================================================

db = FAISS.load_local(
    DB_FAISS_PATH,
    embeddings,
    allow_dangerous_deserialization=True,
)

# ==========================================================
# LLM
# ==========================================================

llm = ChatOpenAI(
    model="llama-3.1-8b-instant",
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=GROQ_API_KEY,
    temperature=0.2,
)

# ==========================================================
# Retrieval Chain
# ==========================================================

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=db.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4
        },
    ),
    chain_type_kwargs={
        "prompt": prompt
    },
)

# ==========================================================
# Chat Start
# ==========================================================

@cl.on_chat_start
async def start():

    cl.user_session.set("chain", qa_chain)

    cl.user_session.set("history", "")

    await cl.Message(
        content="""
# 🩺 MED_GPT

Welcome!

I am an AI Medical Assistant capable of answering medical questions using my medical knowledge base and professional medical reasoning.

For symptom-related questions, I may ask for information such as your age, gender, duration of symptoms, and relevant medical history before providing guidance.

How can I assist you today?
"""
    ).send()

# ==========================================================
# Chat Messages
# ==========================================================

@cl.on_message
async def main(message: cl.Message):

    chain = cl.user_session.get("chain")

    history = cl.user_session.get("history")

    query = message.content

    response = await chain.ainvoke(
        {
            "query": query,
            
        }
    )

    answer = response["result"]

    history += f"\nUser: {query}\nAssistant: {answer}"

    cl.user_session.set("history", history)

    await cl.Message(content=answer).send()