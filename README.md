# 🤖 SwiftCart: Autonomous AI Customer Support & Ticket System
### (With LLM Tool Calling / Function Calling & Live SQLite Database)

A production-style AI Support Agent built specifically to solve real customer service workflows for e-commerce. Unlike simple chatbots that only generate text, this agent uses **LLM Function Calling (Tool Use)** to execute real operations against a backend database (fetching live tracking, cancelling orders, and escalating high-priority tickets).

---

## 🌟 Key Features

1. **Autonomous Tool Calling (Function Calling):**
   - The AI inspects user intent and autonomously invokes backend functions with exact parameters.
   - Built with both **Google Gemini 2.5 Flash** tool execution and a built-in high-fidelity engine.
2. **Real-Time Database Operations:**
   - **`get_order_details(order_id)`**: Queries SQLite for real-time order status, tracking ID, and expected delivery.
   - **`cancel_order(order_id)`**: Verifies if order is cancellable (e.g. Processing vs. Shipped) and updates database state.
   - **`create_support_ticket(priority, description)`**: Detects negative customer sentiment or damaged delivery and creates an escalation ticket.
   - **`get_company_policy(topic)`**: Instant lookup for return, refund, and warranty policies.
3. **Interactive Visual Dashboard:**
   - **Live Chat with Quick Action Prompts** (bilingual: Hindi/Hinglish/English).
   - **Live Database Inspector** (watch orders update from 'Processing' to 'Cancelled' in real-time).
   - **Tool Execution Logs tab** (interviews can see the exact function name, arguments, and JSON payload returned).
   - **One-click DB Reset** for repeated demonstrations.

---

## 🏗️ Architecture Flow

```
[ Customer Chat UI ]
       │
       ▼  (POST /api/chat)
[ FastAPI Backend ]
       │
       ▼  (Analyzes prompt + Tools Schema)
[ LLM / AI Engine ]
       │
       ├─► Wants to check order ──► Calls get_order_details(order_id) ──► [ SQLite DB ]
       ├─► Wants to cancel      ──► Calls cancel_order(order_id)      ──► [ SQLite DB ]
       └─► Angry / Escalation   ──► Calls create_support_ticket(...)  ──► [ SQLite DB ]
       │
       ▼  (LLM receives Tool Result and crafts empathetic final answer)
[ Customer receives Verified Response + Live DB Updates in UI ]
```

---

## 🚀 How to Run

### 1. Requirements
Ensure Python 3.10+ is installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
python run.py
```
Open your browser and navigate to: **`http://localhost:8000`**

*(Optional: If you want to use Google Gemini live, add your free key in `.env` or paste it in the UI navbar modal. If no key is provided, the built-in Smart Agent runs seamlessly!)*

---

## 💼 Resume Description (Copy-Paste Ready)

```text
AI-Powered Support & Ticket Automation System | Python, FastAPI, SQLite, LLM Tool Calling
• Engineered an autonomous customer support agent leveraging LLM Function Calling to eliminate hallucinations and execute direct backend actions.
• Implemented automated order tracking, conditional order cancellations, and sentiment-triggered priority ticket escalation into a live SQLite database.
• Built an interactive inspection dashboard visualizing real-time database state transitions and tool execution payloads for transparency.
```

---

## 🎯 Interview Q&A (How to Pitch this Project)

**Q: Normal Chatbot aur aapke project me kya difference hai?**
> *"Traditional chatbots sirf static text predict karte hain aur fake data hallucinate kar sakte hain. Mere project me LLM ke paas backend tools (functions) ka access hai. Jab user order #101 poochta hai, AI model database se live row fetch karta hai aur us verified data ke base par jawab deta hai."*

**Q: Function Calling / Tool Calling kaise kaam karta hai?**
> *"Hum LLM ko function ka schema aur description dete hain (e.g. `get_order_details(order_id: int)`). LLM user ke prompt ko analyze karta hai, parameter extract karta hai (jaise order_id=101), aur ek structured tool call request return karta hai. Hamara backend us function ko execute karta hai aur output LLM ko wapas bhejta hai taaki wo user ko clean summary de sake."*

**Q: Database safety aur edge cases kaise handle kiye?**
> *"LLM ko direct raw SQL execute karne ki permission nahi di gayi hai taaki SQL injection aur data corruption na ho sake. Iske bajaye deterministic Python functions banaye gaye hain jisme business logic check hoti hai — jaise agar order already 'Shipped' hai, toh cancellation block ho jata hai aur return initiation ka option diya jata hai."*
