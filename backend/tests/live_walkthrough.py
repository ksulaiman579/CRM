import httpx
import sys

def run_walkthrough():
    base_url = "http://localhost:8000/api/v1"
    print("=== STARTING LIVE WALKTHROUGH ===")

    with httpx.Client() as client:
        # 1. Login as agent1
        print("\n[Step 1] Logging in as agent1...")
        login_payload = {
            "username": "agent1",
            "password": "password123"
        }
        r = client.post(f"{base_url}/auth/login", json=login_payload)
        if r.status_code != 200:
            print(f"Error logging in as agent1: {r.status_code} - {r.text}")
            sys.exit(1)
        
        agent_data = r.json()
        agent_token = agent_data["access_token"]
        agent_headers = {"Authorization": f"Bearer {agent_token}"}
        print(f"Successfully logged in as agent1! Token starts with: {agent_token[:15]}...")

        # 2. Find an open ticket
        print("\n[Step 2] Fetching open tickets...")
        r = client.get(f"{base_url}/tickets?status=open", headers=agent_headers)
        if r.status_code != 200:
            print(f"Error fetching open tickets: {r.status_code} - {r.text}")
            sys.exit(1)
        
        res_data = r.json()
        tickets = res_data.get("items", res_data) if isinstance(res_data, dict) else res_data
        
        if not tickets:
            print("No open tickets found to resolve. Checking other non-resolved tickets...")
            r = client.get(f"{base_url}/tickets?status=in_progress", headers=agent_headers)
            res_data = r.json()
            tickets = res_data.get("items", res_data) if isinstance(res_data, dict) else res_data
            if not tickets:
                print("No in_progress tickets found. Creating a temporary ticket to resolve...")
                cust_r = client.get(f"{base_url}/customers", headers=agent_headers)
                cust_res = cust_r.json()
                customers = cust_res.get("items", cust_res) if isinstance(cust_res, dict) else cust_res
                if not customers:
                    print("No customers found either!")
                    sys.exit(1)
                cust_id = customers[0]["id"]
                create_payload = {
                    "customer_id": cust_id,
                    "subject": "Walkthrough Temp Ticket",
                    "description": "Temp description",
                    "category": "technical",
                    "priority": "medium",
                    "channel": "web"
                }
                create_r = client.post(f"{base_url}/tickets", json=create_payload, headers=agent_headers)
                if create_r.status_code != 201:
                    print(f"Failed to create temp ticket: {create_r.text}")
                    sys.exit(1)
                ticket = create_r.json()
            else:
                ticket = tickets[0]
        else:
            ticket = tickets[0]

        ticket_id = ticket["id"]
        ticket_num = ticket.get("ticket_number", f"ID: {ticket_id}")
        print(f"Target ticket selected: {ticket_num} (Subject: {ticket.get('subject')})")

        # 3. Resolve the ticket and submit 5-star CSAT
        print("\n[Step 3] Resolving the ticket with 5-star CSAT...")
        resolve_payload = {
            "status": "resolved",
            "csat_rating": 5,
            "csat_feedback": "Great and fast resolution!"
        }
        r = client.patch(f"{base_url}/tickets/{ticket_id}", json=resolve_payload, headers=agent_headers)
        if r.status_code != 200:
            print(f"Error resolving ticket: {r.status_code} - {r.text}")
            sys.exit(1)
        
        updated_ticket = r.json()
        print("Ticket status successfully updated to resolved!")
        print(f"Saved CSAT Rating: {updated_ticket.get('csat_rating')}")
        print(f"Saved CSAT Feedback: \"{updated_ticket.get('csat_feedback')}\"")

        # 4. Login as supervisor1
        print("\n[Step 4] Logging in as supervisor1...")
        login_payload = {
            "username": "supervisor1",
            "password": "password123"
        }
        r = client.post(f"{base_url}/auth/login", json=login_payload)
        if r.status_code != 200:
            print(f"Error logging in as supervisor1: {r.status_code} - {r.text}")
            sys.exit(1)
        
        super_data = r.json()
        super_token = super_data["access_token"]
        super_headers = {"Authorization": f"Bearer {super_token}"}
        print(f"Successfully logged in as supervisor1! Token starts with: {super_token[:15]}...")

        # 5. Fetch Supervisor Dashboard metrics
        print("\n[Step 5] Querying supervisor dashboard analytics...")
        r = client.get(f"{base_url}/dashboard/supervisor", headers=super_headers)
        if r.status_code != 200:
            print(f"Error fetching supervisor dashboard: {r.status_code} - {r.text}")
            sys.exit(1)
        
        dash_data = r.json()
        print("Dashboard metrics retrieved successfully:")
        print(f" - Average CSAT Score: {dash_data.get('average_csat')}")
        print(f" - CSAT Rating Counts: {dash_data.get('csat_rating_counts')}")

        # 6. Fetch CSAT customer feedback list
        print("\n[Step 6] Querying recent CSAT feedback list...")
        r = client.get(f"{base_url}/dashboard/csat-feedback", headers=super_headers)
        if r.status_code != 200:
            print(f"Error fetching csat feedback list: {r.status_code} - {r.text}")
            sys.exit(1)
        
        feedbacks = r.json()
        print("Recent Feedback Feed:")
        found_our_feedback = False
        for fb in feedbacks[:5]:
            print(f" - [Rating: {fb.get('csat_rating')}] Comment: \"{fb.get('csat_feedback')}\" (Ticket: {fb.get('ticket_number')})")
            if fb.get("ticket_number") == ticket_num or fb.get("csat_feedback") == "Great and fast resolution!":
                found_our_feedback = True

        if found_our_feedback:
            print("\nSUCCESS: Walkthrough verification complete! Live endpoints are fully integrated and functional.")
        else:
            print("\nWARNING: Feedback was submitted successfully but did not appear in the top recent feedback feed.")

if __name__ == "__main__":
    run_walkthrough()
