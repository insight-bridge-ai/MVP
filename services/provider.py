from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from decouple import config
### Connecting to the remoter server
# Replace with your Aura details
NEO4J_URI = config("NEO4J_URI")
NEO4J_USERNAME = config("NEO4J_USERNAME")
NEO4J_PASSWORD = config("NEO4J_PASSWORD")
NEO4J_DATABASE = config("NEO4J_DATABASE")
groq_api_key= config("GROQ_API_KEY")

### loading the knowledge graph
kg = Neo4jGraph(
    url=NEO4J_URI, 
    username=NEO4J_USERNAME, 
    password=NEO4J_PASSWORD, 
    database=NEO4J_DATABASE
)

### loading the llm
groq_llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=groq_api_key
)


### prompt template
cypher_prompt = PromptTemplate(
    template=(
        "You are an expert Neo4j Cypher generator.\n"
        "Follow the schema and few-shot examples to answer the user's query.\n\n"
        "### Schema ###\n"
        "{schema}\n\n"
        "### Examples ###\n"
        "{examples}\n\n"
        "### User Question ###\n"
        "{question}\n\n"
        "Return only Cypher. Do not explain."
    ),
    input_variables=["schema", "examples", "question"]
)


### Examples
few_shot_examples = [
    ("What are the top-selling product categories?",
     "MATCH (o:Order) WITH o, COUNT(*) AS count ORDER BY count DESC LIMIT 1 RETURN o.category"),
    
    ("Which city generates the highest revenue?",
     "MATCH (c:Customer)-[:ORDERED]->(o:Order) WHERE o.reason IS  NULL WITH c, SUM(o.total_amount) AS total_value ORDER BY total_value DESC LIMIT 1 RETURN c.city"),
    
    ("What percentage of orders resulted in returns?",
     "MATCH (o:Order) WITH COUNT(o) AS all MATCH (o:Order) WHERE o.reason IS NOT NULL WITH all, count(o) as ret RETURN  toFloat(ret)/all"),
    
    ("Which campaigns had the best CTR?",
     "MATCH (a:Ad)-[:IN]->(c:Campaign) WITH c, AVG(a.ctr) AS mean_value ORDER BY mean_value DESC LIMIT 1 RETURN c.campaign_id"),
    
    ("During which campaign the most customers joined?",
     "MATCH (p:Campaign) MATCH (e:Customer) WHERE date(e.join_date) >= date(p.start_date) AND date(e.join_date) <= date(p.end_date) WITH p, count(e) AS event_count ORDER BY event_count DESC RETURN p.campaign_id LIMIT 1"),
    
    ("How many Orders were received in October of 2023?",
     "MATCH (o:Order) WHERE date(o.order_date).year = 2023 AND date(o.order_date).month = 10 RETURN count(o) AS orders_in_october"),
    
    ("What was our GMV(Gross merchandise volume) in October of 2023?",
     "MATCH (o:Order) WHERE date(o.order_date).year = 2023 AND date(o.order_date).month = 10 RETURN sum(o.total_amount) AS gmv_octoberr"),
    
    ("From which city did the most people  joined during the most successful campaign?",
     "MATCH (c:Campaign) MATCH (cust:Customer) WHERE date(cust.join_date) >= date(c.start_date) AND date(cust.join_date) <= date(c.end_date) WITH c, count(cust) AS total_joiners ORDER BY total_joiners DESC LIMIT 1 MATCH (cust:Customer) WHERE date(cust.join_date) >= date(c.start_date) AND date(cust.join_date) <= date(c.end_date) WITH c, cust.city AS city, count(cust) AS num_people ORDER BY num_people DESC LIMIT 1 RETURN city"),
    
    ("How many customers joined during campaign 10??",
     "MATCH (cam:Campaign) WHERE cam.campaign_id='10' MATCH (c:Customer) WHERE date(c.join_date)<date(cam.end_date) AND date(c.join_date)< date(cam.start_date) RETURN count(c)")


]

formatted_examples = "\n\n".join(
    f"User: {q}\nCypher: {c}" for q, c in few_shot_examples
)

### Schema
schema="""
Nodes
    (:Ad {{ad_id, campaign_id, impressions, clicks, spend, ctr}})
    (:Campaign {{campaign_id, platform, start_date, end_date, cost,conversions}})
    (:Order {{order_id, customer_id, order_date, product_id, quantity, total_amount, product_name, category, price, stock, reason, return_date, refund_amount}})
    (:Customer {{customer_id, name, gender, city, join_date}})
    (:platform {{platform, platform, platform_id}})
    (:Return_Reason {{reason_id, reason}})
Relationships:
    (Ad)-[:IN]->(Campaign)
    (Campaign)-[:USED_PLATFORM]->(platform)
    (Order)-[:PLACED_DURING]->(Campaign)
    (Order)-[:RETURNED_BECAUSE]->(Return_Reason)
    (Customer)-[:ORDERED]->(Order)
    (Customer)-[:JOINED_DURING]->(Campaign)
Full-text indexes:
ReturnReasonTextSearch on Return_Reason(reason)
    customerTextSearch on Customer(name)
    customercityTextSearch on Customer(city)
    platfomrused2TextSearch on Campaign(platform)
    platfomrusedTextSearch on platform(platform)
    productCategoryTextSearch on Order(category)
    productTextSearch on Order(product_name)
"""


### Answer prompt
answer_prompt = PromptTemplate(
    template="""
Given the Neo4j query results:
{context}

Answer the question in natural language:
{question}
""",
    input_variables=["context", "question"]
)


def graph_qa_natural(question, schema):
    # 1️⃣ Generate Cypher query
    cypher_query = groq_llm.invoke(
        cypher_prompt.format(
            schema=schema,
            examples=formatted_examples,
            question=question
        )
    ).content
    # print("Generated Cypher:", cypher_query)

    # 2️⃣ Execute query on Neo4j
    result = kg.query(cypher_query)
    # print("Neo4j Result:", result)

    # 3️⃣ Generate natural language answer
    answer = groq_llm.invoke(
        answer_prompt.format(context=str(result), question=question)
    ).content

    return answer


def ask_graph(question: str, schema_override: str | None = None) -> str:
    use_schema = schema_override if schema_override is not None else schema
    try:
        return graph_qa_natural(question, use_schema)
    except Exception as e:
        print("Error", e)
        # Return a concise error message suitable for API responses
        return f"Unable to process your question, please refine your question and ask again. ({str(e)})"