import logging

from langchain_groq import ChatGroq

from langchain.chains import RetrievalQA

from langchain.prompts import PromptTemplate

from ..models.vector_store import VectorStoreModel



logger = logging.getLogger(__name__)



AGRIBOT_PROMPT = """You are AgriBot, an expert agricultural assistant specializing in Indian farming and agriculture.



CRITICAL REQUIREMENTS:

- ALWAYS provide a complete response with a proper conclusion

- NEVER end abruptly - always summarize the key takeaways

- Include actionable advice or final recommendations

- Structure: Introduction → Main Points → Conclusion/Summary



Instructions:

- Use the provided context as your PRIMARY source of information

- If context is insufficient, use your agricultural knowledge

- Focus on Indian agriculture, crops, and farming practices

- Be specific, practical, and easy to understand for farmers

- Format your response clearly with bullet points where helpful

- END EVERY RESPONSE with a concluding paragraph that summarizes the main points and provides final advice



Context:

{context}



Farmer's Question:

{question}



Provide a complete answer with proper conclusion:"""





class QAService:



    def __init__(self, config):

        self._config = config

        self._chain  = None



    def pre_initialize(self):

        """Initialize the QA chain at startup to avoid first-request timeout"""

        logger.info("Pre-initializing AgriBot QA service...")

        self._get_chain()

        logger.info("AgriBot QA service pre-initialization complete!")



    def ask(self, query: str) -> str:

        chain  = self._get_chain()

        result = chain.invoke({"query": query})

        return self._extract_answer(result)



    def is_ready(self) -> bool:

        return self._chain is not None



    def _get_chain(self):

        if self._chain is None:

            logger.info("Building QA chain...")

            self._chain = self._build_chain()

        return self._chain



    def _build_chain(self):

        cfg = self._config



        vector_model = VectorStoreModel(cfg)

        vectorstore  = vector_model.get_or_build()



        retriever = vectorstore.as_retriever(

            search_type="similarity",

            search_kwargs={"k": cfg.RETRIEVER_K}

        )



        logger.info("Initializing Groq LLM...")

        llm = ChatGroq(

            model=cfg.GROQ_MODEL,

            temperature=cfg.LLM_TEMPERATURE,

            max_tokens=cfg.LLM_MAX_TOKENS,

            groq_api_key=cfg.GROQ_API_KEY

        )



        prompt = PromptTemplate(

            template=AGRIBOT_PROMPT,

            input_variables=["context", "question"]

        )



        logger.info("Creating QA chain...")

        chain = RetrievalQA.from_chain_type(

            llm=llm,

            chain_type="stuff",

            retriever=retriever,

            return_source_documents=False,

            chain_type_kwargs={"prompt": prompt}

        )



        logger.info("AgriBot QA chain is ready!")

        return chain



    def _extract_answer(self, response) -> str:

        if isinstance(response, dict):

            answer = (

                response.get("result") or

                response.get("answer") or

                response.get("output") or

                str(response)

            )

        else:

            answer = str(response)

        

        answer = answer.strip() or "I couldn't generate a response. Please rephrase."

        

        # Ensure response has proper ending

        answer = self._ensure_complete_response(answer)

        

        return answer

    

    def _ensure_complete_response(self, response: str) -> str:

        """Ensure response has proper ending and is not truncated"""

        response = response.strip()

        

        # Check for incomplete sentences/points

        incomplete_indicators = [

            "1.", "2.", "3.", "4.", "5.",  # Numbered lists without content

            "•", "-", "*",               # Bullet points without content

            "Additional Tips:", "Note:", "Important:",  # Headers without content

            "The", "This", "That", "It",  # Sentences starting but not ending

            "and", "but", "or", "so",     # Conjunctions suggesting continuation

        ]

        

        # If response ends with incomplete indicators, add proper ending

        for indicator in incomplete_indicators:

            if response.endswith(indicator):

                response += " Please ask for more specific details about this topic."

                break

        

        # Ensure response ends with proper punctuation

        if response and response[-1] not in {'.', '!', '?'}:

            response += '.'

            

        return response