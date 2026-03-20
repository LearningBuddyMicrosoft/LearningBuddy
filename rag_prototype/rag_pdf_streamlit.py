# To run this file 
#streamlit run rag_pdf_streamlit.py

import tempfile
import streamlit as st

#Let's us talk to local Llama Model
from langchain_community.chat_models import ChatOllama

#PDF Loader lets us extract text from the document
from langchain_community.document_loaders import PyPDFLoader

#Helps us break text into chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter

#Converts chunks into numerical vectors
from langchain_community.embeddings import OllamaEmbeddings

#Chunks that have become vectors are stored in this Chroma database
from langchain_community.vectorstores import Chroma

#Allows us structure prompt
from langchain_core.prompts import ChatPromptTemplate

#This strings everything together
from langchain_core.runnables import RunnablePassthrough

MODEL_NAME = "llama3.1"

# --- LLM  + Embeddings--- #

#Helper Function 1
#Temperature controls how random the next token will be
#Low Temperature (0.0 - 0.3) will pick the most likely words almost every time
#Suitable for our needs

@st.cache_resource
def get_llm():
    return ChatOllama(model=MODEL_NAME, temperature=0.2)


#Helper Function 2
#Returns embedding model turning each chunk into a vector

@st.cache_resource
def get_embeddings():
    return OllamaEmbeddings(model=MODEL_NAME)

# --- RAG Helper Functions --- #

#Simply put, it takes the PDF and turns it into vector store

def build_vectorstore_from_pdf(uploaded_file):
    #If file doesn't exist print error message
    if uploaded_file is None:
        raise ValueError("No PDF Provided")
    
    #If file does exist, save it to a proper file path temporarily 
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

        #Load PDF
        loader = PyPDFLoader(tmp_path)

        #Extract text from each page 
        docs = loader.load()

        #If nothing can be extracted show error message
        if not docs:
            raise ValueError("Could not extract any text from the PDF")
        
        #Create text splitter, break document into chunks of around 800 characters
        #Overlap helps preserve context across chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size = 800,
            chunk_overlap=150,
            add_start_index=True,
        )
        #Embed chunks using embedding model
        chunks = splitter.split_documents(docs)

        if not chunks:
            raise ValueError("Chunking produced no chunks. Check PDF content")
        
        #Store everything inside a Chroma Vector Database
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=get_embeddings(),
        )
        return vectordb
    
    #This function takes in the vector store, number of chunks to retrieve and preferred answer style

def make_rag_chain(vectordb, k: int, answer_style: str):

    #Convert vector store into a retriever
    #Its job is to look at the user's question and pull the top 'k' most relevant chunks
    retriever = vectordb.as_retriever(search_kwargs={"k": k})

    #Take the user's question and use the retriever to fetch the relevant chunks then join them together
    def join_context(question: str) -> str:
        docs = retriever.invoke(question)

        #If nothing relevant is found return an error message
        if not docs:
            return "No relevant context found in the document"
        return "\n\n---\n\n".join(d.page_content for d in docs)
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful assistant that answers questions based ONLY on the given PDF.

        If the answer is not clealy in the PDF say:
        "I don't see any relevant content that can lead to an answer."

        User prefers : {answer_style} answers.
        Use the context to answer clearly.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
    )

    llm = get_llm()
    #LangChain pipeline
    rag_chain=(
        {
            #Pass the user's question
            "question": RunnablePassthrough(),
            #Retrieves relevant chunks and joins them into one string
            "context": join_context,

            "answer_style": lambda _: answer_style,
        }

        |prompt
        |llm #Sends prompt to Ollama
    )
    return rag_chain, retriever

#--- Streamlit UI ---#

#Set up persistent memory so that every time we click a button it doesn't reset
def init_session():
    
    #Check if vectordb exists in memory, if not set it to none
    if "vectordb" not in st.session_state:
        st.session_state.vectordb = None

        #Chat history storage,
        #Create an empty list to store conversations.
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def main():
    #Set page title, icon and layout
    st.set_page_config(
        page_title = "RAG Prototype",
        page_icon="📄",
        layout="wide",
    )
    init_session()

    #Displays a header at the top of the page
    st.title("📄 Ask a Question!")
    st.caption(
        "Upload a PDF, we'll build a local vector store, and you can ask questions "
        "grounded in document. Runs locally with Ollama"
    )

    #--- Sidebar: Settings & Reset ---#
    #This is where we start to add structure
    #Put everything in this code block into the sidebar
    with st.sidebar:
        st.header("⚙️RAG Settings")

        #Streamlit slider UI component
        top_k = st.slider("Top-k chunks to retrieve", min_value=1, max_value=8, value=4)

        #Dropdown menu to choose answer style
        answer_style = st.selectbox(
            "Answer style",
            ["Short and crisp", "Detailed"],
            index=0,
        )
        #Clear memory
        if st.button(" Clear Chat and Reset"):
            st.session_state.chat_history = []
            st.session_state.vectordb = None
            st.success("State cleared. Upload a PDF again.")


    col_left, col_right = st.columns([1, 2])


    # ---Left Side of UI PDF Uploading and Processes--- #
    #Everything in this code block goes to the left of the page
    with col_left:
        st.subheader("Upload & Process PDF")

        #Create drag and drop box / browse file box
        uploaded_file = st.file_uploader(
            "Upload a PDF File",
            type=["pdf"], #Only allow PDF
            help="Keep it small for faster demo."
        )
        #Create button to start processing pdf
        #On Streamlit buttons return true when clicked, false otherwise
        if st.button("Process PDF"):
            if uploaded_file is None:
                st.warning("Please upload a PDF first")

            else:
                try:
                    #Spinner shows a loading animation while work is happening
                    with st.spinner("Reading, chunking, and embedding yout PDF..."):
                        vectordb = build_vectorstore_from_pdf(uploaded_file)

                        #Very Important, makes the database available across the app
                        st.session_state.vectordb = vectordb

                        #Error handling
                    st.success("PDF processed! You can start asking questions")
                except Exception as e:
                    st.error(f"Error while processing PDF: {e}")


        #No PDF loaded message
        if st.session_state.vectordb is None:
            st.info("Upload a PDF and click **Process PDF** to get started")

        st.markdown("---") #Draws a Line


    # ---Right Side of UI Q&A Chat-- #
    #Everything in this code block goes into the right side of the UI
    with col_right:
        st.subheader("Ask Questions about your PDF")

        #Stops everything if no PDF is loaded
        if st.session_state.vectordb is None:
            st.warning("No PDF processed yet. Upload and process a file on the Left.")
            return
        
        #Question Input Box
        question = st.text_input(
            "Type your question",
            placeholder="Example: What are the key takeaways of this document?",
        )

        #Again, returns true if clicked and false otherwise
        ask_clicked = st.button("Ask")

        #Runs if user clicked and question is not empty
        #.strip() removes all whitespace
        # Uses truthiness,  empty string is false, string with at least one char is true
        if ask_clicked and question.strip():
            try:
                rag_chain, retriever = make_rag_chain(
                    st.session_state.vectordb,
                    k=top_k,
                    answer_style=answer_style,
                )

                with st.spinner("Thinking with RAG...."):
                    #Generate Response
                    res = rag_chain.invoke(question)
                    #Built in python function getattr(object, "attribute_name", fallback_value)
                    #Check res.content else str(res)
                    answer = getattr(res, "content", str(res))

                    docs = retriever.invoke(question)
                    #Create a list called sources
                    sources = []
                    #Iterate through document and append
                    for d in docs:
                        sources.append(
                            {
                                "page": d.metadata.get("page", "?"), #Page number
                                "snippet":d.page_content[:400] + ("..." if len(d.page_content) > 400 else ""),#Snippet first 400 characters of chunk
                            }
                        )
                        #Save to chat history
                st.session_state.chat_history.append(
                    {"q": question, "a": answer, "sources": sources}
                )
                #Prevents app crashing
            except Exception as e:
                st.error(f"Error while generating answer: {e}")
        #Display chat history, newest messages appear at the top
        for item in reversed(st.session_state.chat_history):
            with st.chat_message("user"): #Streamlit renders user bubble, just for UI clarity
                st.markdown(item["q"])

            with st.chat_message("assistant"): #Streamlit renders assitant bubble
                st.markdown(item["a"])
                if item["sources"]:
                    with st.expander("View sources from PDF"): #Streamlit creates an expanable dropdown
                        for i, s in enumerate(item["sources"], start=1):
                            st.markdown(
                                f"**Source {i}** - Page `{s['page']}`\n\n"
                                f"{s['snippet']}\n"
                                "---"
                            )

if __name__== "__main__":
    main()