import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from backend.database import init_db, get_db_connection
from backend.agent import run_agent_turn

def run_tests():
    print("1. Initializing DB...")
    conn = get_db_connection()
    conn.execute("DROP TABLE IF EXISTS orders")
    conn.execute("DROP TABLE IF EXISTS tickets")
    conn.commit()
    conn.close()
    init_db()
    
    print("\n2. Testing Order Tracking tool...")
    res1 = run_agent_turn("Order #101 ka status kahan hai?")
    print("Bot Reply:", res1["reply"])
    print("Tools Called:", res1["tool_calls"])
    assert len(res1["tool_calls"]) > 0
    assert res1["tool_calls"][0]["tool"] == "get_order_details"

    print("\n3. Testing Cancellation tool...")
    res2 = run_agent_turn("Mujhe order #102 cancel karna hai")
    print("Bot Reply:", res2["reply"])
    print("Tools Called:", res2["tool_calls"])
    assert len(res2["tool_calls"]) > 0
    assert res2["tool_calls"][0]["tool"] == "cancel_order"

    # Verify DB update
    conn = get_db_connection()
    row = conn.execute("SELECT status FROM orders WHERE order_id = 102").fetchone()
    print("DB Status for order 102:", row["status"])
    assert row["status"] == "Cancelled"
    conn.close()

    print("\n4. Testing Ticket Escalation tool...")
    res3 = run_agent_turn("Mera parcel toota hua aaya hai, 5 din se koi sun nahi raha, I want a refund now!")
    print("Bot Reply:", res3["reply"])
    print("Tools Called:", res3["tool_calls"])
    assert len(res3["tool_calls"]) > 0
    assert res3["tool_calls"][0]["tool"] == "create_support_ticket"

    print("\n>>> ALL TESTS PASSED! System is functioning 100% correctly.")

if __name__ == "__main__":
    run_tests()
