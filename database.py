from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Supabase client with error handling
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Supabase client initialized successfully")
except Exception as e:
    print(f"Failed to initialize Supabase client: {e}")
    print(f"SUPABASE_URL exists: {bool(os.getenv('SUPABASE_URL'))}")
    print(f"SUPABASE_KEY exists: {bool(os.getenv('SUPABASE_KEY'))}")
    raise

def get_all_drivers():
    """Get all drivers"""
    response = supabase.table("drivers").select("*").order("created_at", desc=True).execute()
    return response.data

def get_driver_by_id(driver_id: str):
    """Get single driver by ID"""
    response = supabase.table("drivers").select("*").eq("id", driver_id).single().execute()
    return response.data

def get_load_by_id(load_id: str):
    """Get single load by ID"""
    try:
        response = supabase.table("loads").select("*").eq("id", load_id).single().execute()
        return response.data
    except Exception as e:
        print(f"❌ Error getting load by ID: {e}")
        return None

def get_driver_by_phone(phone: str):
    """Get driver by phone number"""
    try:
        response = supabase.table("drivers").select("*").eq("phone", phone).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f" Database error getting driver by phone: {e}")
        return None

def get_available_loads():
    """Get all available loads"""
    response = supabase.table("loads").select("*").eq("status", "available").order("created_at", desc=True).execute()
    return response.data

def update_driver_status(driver_id: str, is_loaded: bool, location: str, reason: str = None):
    """Update driver status and log the change"""
    # Update driver table
    supabase.table("drivers").update({
        "is_loaded": is_loaded,
        "current_location": location
    }).eq("id", driver_id).execute()
    
    # Insert into driver_status history
    supabase.table("driver_status").insert({
        "driver_id": driver_id,
        "is_loaded": is_loaded,
        "location": location,
        "notes": reason
    }).execute()

def create_call_log(driver_id: str, is_loaded: bool, reason: str, location: str, call_sid: str = None):
    """Create a call log entry"""
    supabase.table("call_logs").insert({
        "driver_id": driver_id,
        "call_sid": call_sid,
        "is_loaded": is_loaded,
        "reason_not_loaded": reason,
        "current_location": location
    }).execute()

def get_call_logs():
    """Get recent call logs with driver info"""
    response = supabase.table("call_logs").select("*, drivers(name, phone)").order("created_at", desc=True).limit(50).execute()
    return response.data

def assign_load_to_driver(load_id: str, driver_id: str):
    """Assign a load to a driver"""
    supabase.table("loads").update({
        "status": "assigned",
        "assigned_driver_id": driver_id
    }).eq("id", load_id).execute()
    
    # Update driver status
    supabase.table("drivers").update({
        "is_loaded": True
    }).eq("id", driver_id).execute()

def update_load_assignment_status(load_id: str, driver_id: str, status: str, reason: str, estimated_pickup: str, concerns: str):
    """Update load assignment status based on driver response"""
    try:
        # Update load status based on driver response
        if status == "accepted":
            load_status = "confirmed"
        elif status == "rejected":
            load_status = "available"  # Make available for reassignment
        else:
            load_status = "pending"  # Needs discussion
        
        supabase.table("loads").update({
            "status": load_status,
            "driver_response": status,
            "response_reason": reason,
            "estimated_pickup": estimated_pickup,
            "driver_concerns": concerns
        }).eq("id", load_id).execute()
        
        print(f"✅ Load {load_id} status updated to {load_status}")
        
    except Exception as e:
        print(f"❌ Error updating load assignment: {e}")

def create_load_assignment_log(driver_id: str, load_id: str, status: str, reason: str, concerns: str, call_sid: str = None):
    """Create a log entry for load assignment call"""
    try:
        supabase.table("call_logs").insert({
            "driver_id": driver_id,
            "call_sid": call_sid,
            "call_type": "load_assignment",
            "load_id": load_id,
            "assignment_status": status,
            "reason_not_loaded": reason,
            "driver_concerns": concerns,
            "current_location": "N/A"
        }).execute()
        
        print(f"✅ Load assignment call logged")
        
    except Exception as e:
        print(f"❌ Error creating load assignment log: {e}")
