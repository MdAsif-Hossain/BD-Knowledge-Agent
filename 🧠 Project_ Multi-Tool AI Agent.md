## **🧠 Project: Multi-Tool AI Agent for Bangladesh**

### **🎯 Objective**

Build an AI Agent that can:

* Answer **data-specific queries** from three Bangladesh datasets:  
  * Institutional Information  
  * Hospitals  
  * Restaurants  
* Use a **Web Search Tool** for general knowledge (e.g., definitions, policies, cultural context).

## **📁 Provided Datasets**

We’ll use these HuggingFace datasets:

**Institutional Information of Bangladesh**  

* 🔗 https://huggingface.co/datasets/Mahadih534/Institutional-Information-of-Bangladesh

**All Bangladeshi Hospitals**  

* 🔗 https://huggingface.co/datasets/Mahadih534/all-bangladeshi-hospitals

**Bangladeshi Restaurant Data**  

* 🔗 https://huggingface.co/datasets/Mahadih534/Bangladeshi-Restaurant-Data

## **🛠️ Project Tasks**

### **1\. Convert CSVs to SQLite DBs**

For each dataset, create a SQLite database:

* `institutions.db` → Table: `institutions`  
* `hospitals.db` → Table: `hospitals`  
* `restaurants.db` → Table: `restaurants`

Make sure:

* Column names are meaningful (`name`, `location`, `type`, `capacity`, etc.)  
* Column types are set correctly (`TEXT`, `INTEGER`, `REAL`).

### **2\. Build DB-specific Tools**

Create LangChain tools for each DB:

* **InstitutionsDBTool** → Queries about universities, colleges, govt institutions.  
* **HospitalsDBTool** → Queries about hospitals, beds, doctors, facilities.  
* **RestaurantsDBTool** → Queries about restaurants, cuisine, ratings, locations.

Each tool:

* Connects to its DB  
* Executes SQL queries  
* Returns results in **natural language**.

### **3\. Add a Web Search Tool**

**WebSearchTool → General knowledge**  

* Example: “What is the healthcare policy in Bangladesh?”  
* Uses **SerpAPI / Tavily / Bing API  / any search tool**.

### **4\. Main AI Agent Logic**

Build a **Main Agent** with LangChain Agent Executor:

🧮 **Data/statistics queries** → Route to DB tools

* Example: “How many hospitals are in Dhaka?” → `HospitalsDBTool`

🌐 **General knowledge queries** → Route to Web Search tool

* Example: “What is the role of DGHS in Bangladesh?” → `WebSearchTool`

## **📦 Submission Requirements**

* **GitHub Repo** with full codebase  
* **README** with instructions  
* Optional: **Google Colab link** for demo

## **🔍 Example Queries (Might not related to the provided db)**

| Query | Tool Used | Example Answer |
| ----- | ----- | ----- |
| “List top 10 hospitals in Dhaka with bed capacity.” | HospitalsDBTool | Returns hospital names \+ bed counts |
| “Which universities in Bangladesh offer medical degrees?” | InstitutionsDBTool | Returns list of institutions |
| “Find restaurants in Chattogram serving biryani.” | RestaurantsDBTool | Returns restaurant names \+ addresses |
| “What is the healthcare policy of Bangladesh?” | WebSearchTool | Returns web-based info |
| “How many government institutions are in Rajshahi?” | InstitutionsDBTool | Returns count |

