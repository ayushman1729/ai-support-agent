import os
import re
import json
from dotenv import load_dotenv
from backend.tools import (
    get_order_details,
    cancel_order,
    create_support_ticket,
    get_company_policy,
    AVAILABLE_TOOLS
)

load_dotenv()

SYSTEM_PROMPT = """
You are an intelligent, empathetic, and highly capable Customer Support AI for an e-commerce platform called 'SwiftCart'.
Your goal is to assist customers with order status, order cancellation, returns/refund policy questions, and escalate severe issues by creating support tickets.

You have access to the following backend tools/functions:
1. `get_order_details(order_id: int)`: Checks live order status, tracking, and delivery estimate from the database.
2. `cancel_order(order_id: int, reason: str)`: Cancels an order if it is in 'Processing' or 'Placed' status.
3. `create_support_ticket(customer_name: str, issue_description: str, priority: str, order_id: int)`: Creates an escalated ticket if the user is dissatisfied, experiencing delays, or has broken items.
4. `get_company_policy(topic: str)`: Provides official company policy regarding returns, refunds, warranty, and shipping.

Instructions:
- When a user asks about an order or provides an order number, ALWAYS call `get_order_details` to verify live facts from the database before answering.
- If a user asks to cancel an order, call `cancel_order`.
- If the user is angry, facing an unresolved defect, or requests human help, create a ticket using `create_support_ticket` with appropriate priority ('MEDIUM', 'HIGH', or 'CRITICAL').
- Speak in a polite, helpful, and natural tone (Hinglish or English matching the user's language).
- Never hallucinate fake order details.
"""

def run_agent_turn(user_message: str, history: list = None, api_key: str = None) -> dict:
    """
    Executes a turn of the conversation.
    Returns:
    {
        "reply": str,
        "tool_calls": list of dicts [{"tool": name, "args": {...}, "output": {...}}],
        "mode": "gemini" | "simulator"
    }
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if key:
        try:
            return _run_with_gemini(user_message, history or [], key)
        except Exception as e:
            print(f"[Gemini Error, falling back to simulator]: {e}")
            fallback_res = _run_with_simulator(user_message, history or [])
            fallback_res["reply"] += f"\n\n*(Note: Gemini API fallback engaged: {str(e)[:100]}...)*"
            return fallback_res
    else:
        return _run_with_simulator(user_message, history or [])

def _run_with_gemini(user_message: str, history: list, api_key: str) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    tool_calls_executed = []

    # Configure tool functions
    tools_list = [get_order_details, cancel_order, create_support_ticket, get_company_policy]

    # Convert simple history into gemini contents
    contents = []
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg.get("content", ""))]
        ))
    
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)]
    ))

    # Turn 1: Model sees user message and decides whether to call tools
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=tools_list,
        temperature=0.3
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config
    )

    # Check if any function call was requested
    if response.function_calls:
        for call in response.function_calls:
            fn_name = call.name
            fn_args = dict(call.args) if call.args else {}

            if fn_name in AVAILABLE_TOOLS:
                tool_result = AVAILABLE_TOOLS[fn_name](**fn_args)
                tool_calls_executed.append({
                    "tool": fn_name,
                    "args": fn_args,
                    "output": tool_result
                })

                # Append model's tool call part
                contents.append(response.candidates[0].content)

                # Append function response part
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name=fn_name,
                        response={"result": tool_result}
                    )]
                ))

        # Turn 2: Model sees function execution result and crafts final user-facing response
        followup_resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )
        return {
            "reply": followup_resp.text or "Here is the requested information.",
            "tool_calls": tool_calls_executed,
            "mode": "gemini"
        }
    else:
        return {
            "reply": response.text or "How can I assist you with your order today?",
            "tool_calls": [],
            "mode": "gemini"
        }

def _run_with_simulator(user_message: str, history: list) -> dict:
    """
    Intelligent built-in Tool Calling simulator.
    Recognizes customer intent (tracking, cancellation, complaint/ticket, policies, option numbers)
    and executes the exact same backend database tools.
    """
    msg_clean = user_message.strip()
    msg_lower = msg_clean.lower()
    tool_calls = []
    reply = ""

    # Check previous assistant message to maintain conversational context
    last_assistant_msg = ""
    for msg in reversed(history or []):
        if msg.get("role") in ["assistant", "model"]:
            last_assistant_msg = msg.get("content", "").lower()
            break

    # Extract order number: like #101, order 102, or standalone 3-digit number
    order_id = None
    order_id_match = re.search(r'(?:order\s*#?|#)(\d{2,4})', msg_lower)
    if not order_id_match:
        order_id_match = re.search(r'\b(\d{3})\b', msg_lower)
    
    if order_id_match:
        order_id = int(order_id_match.group(1))

    # Contextual check: if previous question asked for Order ID, and user just gave a number
    if not order_id and re.fullmatch(r'\d{2,4}', msg_clean):
        order_id = int(msg_clean)

    # 1. Check if user selected a menu option number: 1, 2, 3, or 4
    if msg_clean in ["1", "option 1", "opt 1", "first"]:
        return {
            "reply": "Aap kis Order ID ka status check karna chahte hain? Kripya apna Order ID share karein (jaise #101, #102, ya #103).",
            "tool_calls": [],
            "mode": "simulator"
        }
    elif msg_clean in ["2", "option 2", "opt 2", "second"]:
        return {
            "reply": "Aap kaunsa order cancel karna chahte hain? Kripya apna Order ID batayein (jaise #101 ya #102).",
            "tool_calls": [],
            "mode": "simulator"
        }
    elif msg_clean in ["3", "option 3", "opt 3", "third"]:
        policy_text = get_company_policy(topic="refund")
        tool_calls.append({"tool": "get_company_policy", "args": {"topic": "refund"}, "output": policy_text})
        return {
            "reply": f"SwiftCart ki Return aur Refund Policy:\n\n{policy_text}\n\nAgar aap kisi delivered order ka return raise karna chahte hain, toh apna Order ID batayein.",
            "tool_calls": tool_calls,
            "mode": "simulator"
        }
    elif msg_clean in ["4", "option 4", "opt 4", "fourth"]:
        return {
            "reply": "Kripya apni pareshani batayein taaki mai hamari senior escalation team ke liye Priority Support Ticket generate kar sakoon.",
            "tool_calls": [],
            "mode": "simulator"
        }

    # Intent A: Cancellation
    is_cancel_intent = any(k in msg_lower for k in ["cancel", "cancle", "band karo", "hatao", "nahi chahiye", "cancel karna"])
    # Also if last message asked for order to cancel and user provided order_id
    if ("cancel" in last_assistant_msg and order_id) or is_cancel_intent:
        if order_id:
            res = cancel_order(order_id=order_id, reason="Customer requested via support chat")
            tool_calls.append({"tool": "cancel_order", "args": {"order_id": order_id, "reason": "Customer request"}, "output": res})
            if res.get("success"):
                reply = f"Aapka Order #{order_id} successfully cancel kar diya gaya hai! Refund 24 ghante ke andar aapke original payment mode par credit ho jayega."
            else:
                reply = f"Order #{order_id} cancel nahi kiya ja sakta: {res.get('message')}"
        else:
            reply = "Aap kaunsa order cancel karna chahte hain? Kripya apna Order ID (jaise #101 ya #102) share karein."

    # Intent B: Order Tracking / Where is my order
    elif any(k in msg_lower for k in ["status", "kaha", "kahan", "kidhar", "track", "delivery", "kab aayega", "order detail", "where is", "mera order", "kab tak", "deliver"]):
        if order_id:
            res = get_order_details(order_id=order_id)
            tool_calls.append({"tool": "get_order_details", "args": {"order_id": order_id}, "output": res})
            if "error" in res:
                reply = f"Maaf kijiyega, {res['error']}"
            else:
                reply = (
                    f"Aapke Order #{res['order_id']} ({res['item_name']}) ki details mil gayi hain:\n"
                    f"- Status: {res['status']}\n"
                    f"- Courier Partner: {res.get('courier') or 'N/A'}\n"
                    f"- Tracking ID: {res.get('tracking_id') or 'N/A'}\n"
                    f"- Expected Delivery: {res.get('estimated_delivery') or 'N/A'}\n"
                    f"- Total Amount: Rs. {res.get('total_amount'):,.2f}"
                )
        else:
            reply = "Aap kis order ka status dekhna chahte hain? Kripya apna Order ID batayein (jaise #101, #102, ya #103)."

    # Intent C: Complaint / Anger / Escalation
    elif any(k in msg_lower for k in ["gussa", "angry", "bekar", "fraud", "complaint", "ticket", "human", "agent", "scam", "late", "damage", "defective", "toota", "kharab", "worst", "ghatiya", "koi sun nahi"]):
        priority = "CRITICAL" if any(w in msg_lower for w in ["fraud", "scam", "police", "court"]) else "HIGH"
        customer = "Valued Customer"
        issue = user_message
        res = create_support_ticket(customer_name=customer, issue_description=issue, priority=priority, order_id=order_id)
        tool_calls.append({"tool": "create_support_ticket", "args": {"customer_name": customer, "issue_description": issue, "priority": priority, "order_id": order_id}, "output": res})
        reply = (
            f"Humein bohot afsos hai ki aapko pareshani hui! Maine aapke liye ek **{priority} Priority Ticket (#{res['ticket_id']})** generate kar diya hai.\n\n"
            f"Hamari Senior Escalation Support Team agle 15-30 minute ke andar aapse contact karegi."
        )

    # Intent D: Policy inquiries
    elif any(k in msg_lower for k in ["refund", "return", "warranty", "policy", "guarantee"]):
        topic = "refund" if "refund" in msg_lower or "return" in msg_lower else ("warranty" if "warranty" in msg_lower else "shipping")
        policy_text = get_company_policy(topic=topic)
        tool_calls.append({"tool": "get_company_policy", "args": {"topic": topic}, "output": policy_text})
        reply = f"SwiftCart ki Policy ke mutabiq:\n\n{policy_text}\n\nAgar aap kisi specific order ke liye return/refund chahte hain, toh kripya apna Order ID batayein."

    # Intent E: If user directly enters just the order number (e.g. 101 or #101)
    elif order_id:
        res = get_order_details(order_id=order_id)
        tool_calls.append({"tool": "get_order_details", "args": {"order_id": order_id}, "output": res})
        if "error" in res:
            reply = f"Maaf kijiyega, {res['error']}"
        else:
            reply = (
                f"Aapke Order #{res['order_id']} ({res['item_name']}) ka live status mil gaya hai:\n"
                f"- Status: {res['status']}\n"
                f"- Courier: {res.get('courier') or 'N/A'}\n"
                f"- Expected Delivery: {res.get('estimated_delivery') or 'N/A'}\n\n"
                f"Kya aap is order ko cancel karna chahte hain ya koi aur jankari chahiye?"
            )

    # Intent F: Greeting / General
    else:
        reply = (
            "Namaste! Mai SwiftCart ka AI Support Agent hoon.\n"
            "Mai aapki in cheezon me madad kar sakta hoon:\n"
            "1. Order Status check karna (e.g., 'Order #101 kaha hai?')\n"
            "2. Order Cancel karna (e.g., 'Cancel order #102')\n"
            "3. Return aur Refund policy janna\n"
            "4. Senior Support Team ke liye Priority Ticket banana\n\n"
            "Aap upar diye gaye options me se number (1, 2, 3, 4) bhej sakte hain ya apna sawaal pooch sakte hain!"
        )

    return {
        "reply": reply,
        "tool_calls": tool_calls,
        "mode": "simulator"
    }

    return {
        "reply": reply,
        "tool_calls": tool_calls,
        "mode": "simulator"
    }
