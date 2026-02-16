# chat2.py - GROQ VERSION

from langchain_groq import ChatGroq  # Change this import
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file!")

def setup_chain():
    """Initialize and return the QA chain"""
    
    # ... (keep all the document loading code same) ...
    
    # URLs for web scraping
    urls = [
        "https://www.agricultureinformation.com/",
        "https://vikaspedia.in/agriculture",
        "https://www.fao.org/home/en/",
    ]
    
    # Load web documents
    print("Loading web documents...")
    web_docs = []
    for url in urls:
        try:
            loader = WebBaseLoader(url)
            web_docs.extend(loader.load())
            print(f"✓ Loaded: {url}")
        except Exception as e:
            print(f"✗ Failed to load {url}: {e}")
    
    # Load PDF documents
    print("Loading PDF documents...")
    try:
        pdf_loader = DirectoryLoader(
            './Data/',
            glob="**/*.pdf",
            loader_cls=PyPDFLoader
        )
        pdf_docs = pdf_loader.load()
        print(f"✓ Loaded {len(pdf_docs)} PDF documents")
    except Exception as e:
        print(f"✗ Failed to load PDFs: {e}")
        pdf_docs = []
    
    # Combine all documents
    all_docs = web_docs + pdf_docs
    print(f"Total documents: {len(all_docs)}")
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(all_docs)
    print(f"Created {len(splits)} text chunks")
    
    # Create embeddings
    print("Creating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Create vector store
    print("Creating vector store...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    
    # ✓ GROQ LLM INITIALIZATION (FREE!)
    print("Initializing Groq LLM...")
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",  # Fast and powerful
        temperature=0.1,
        max_tokens=512,
        groq_api_key=GROQ_API_KEY
    )
    
    # Create prompt template
    prompt_template = """You are AgriGenius, an expert agricultural assistant. Use the following context to answer the farmer's question accurately and helpfully.

Context: {context}

Question: {question}

Answer the question based on the context provided. If you don't know the answer, say so politely.

Answer:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # Create retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )
    
    # Create QA chain
    print("Creating QA chain...")
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    print("✓ Groq chain setup complete!")
    return chain

# Create the chain
try:
    qa_chain = setup_chain()
    print("✓ AgriGenius with Groq is ready!")
except Exception as e:
    print(f"✗ Error setting up chain: {e}")
    qa_chain = None


