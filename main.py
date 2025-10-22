from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import sys
import database as db
import vapi_handler
from models import MakeCallRequest, CallWebhook

app = FastAPI(
    title="Hemut Voice AI API",
    description="AI-powered driver status checking system",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Check if all required environment variables are set"""
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "VAPI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"❌ Missing environment variables: {missing_vars}"
        print(error_msg, file=sys.stderr)
        # Don't raise error in production, just log it
        print("⚠️ Warning: Some environment variables are missing")
    else:
        print("✅ All required environment variables are set")
    
    print(f"✅ FastAPI startup complete on port {os.getenv('PORT', '8000')}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://voice-ai-hemut-frontend.vercel.app",
        "*"  # Keep for development, remove in production for security
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Hemut Voice AI API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/drivers",
            "/api/loads",
            "/api/call-logs",
            "/api/make-call",
            "/api/vapi/webhook"
        ]
    }

@app.get("/api/drivers")
def get_drivers():
    """Get all drivers with their current status"""
    try:
        drivers = db.get_all_drivers()
        return {
            "success": True,
            "count": len(drivers),
            "drivers": drivers
        }
    except Exception as e:
        print(f"❌ Error getting drivers: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/loads")
def get_loads():
    """Get all available loads"""
    try:
        loads = db.get_available_loads()
        return {
            "success": True,
            "count": len(loads),
            "loads": loads
        }
    except Exception as e:
        print(f"❌ Error getting loads: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/call-logs")
def get_logs():
    """Get recent call history with driver details"""
    try:
        logs = db.get_call_logs()
        return {
            "success": True,
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        print(f"❌ Error getting logs: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assign-load", tags=["Load Management"], summary="Assign Load to Driver")
async def assign_load(request: Request):
    """
    Assign a specific load to a driver and initiate AI call with load details.
    
    Expected payload: {"driver_id": "uuid", "load_id": "uuid"}
    """
    try:
        body = await request.json()
        driver_id = body.get("driver_id")
        load_id = body.get("load_id")
        
        if not driver_id or not load_id:
            raise HTTPException(status_code=400, detail="Both driver_id and load_id are required")
        
        # Get driver and load details
        driver = db.get_driver_by_id(driver_id)
        load = db.get_load_by_id(load_id)
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        if not load:
            raise HTTPException(status_code=404, detail="Load not found")
        if load.get('status') != 'available':
            raise HTTPException(status_code=400, detail="Load is not available for assignment")
        
        # Assign load to driver
        db.assign_load_to_driver(load_id, driver_id)
        
        # Make AI call with load details
        call_response = await vapi_handler.create_load_assignment_call(
            driver['phone'],
            driver['name'],
            driver['id'],
            load
        )
        
        return {
            "success": True,
            "message": f"Load {load.get('load_number', load_id)} assigned to {driver['name']}",
            "call_id": call_response.get('id'),
            "assignment": {
                "driver": driver['name'],
                "load": load.get('load_number', load_id),
                "pickup": load.get('pickup_location'),
                "delivery": load.get('delivery_location')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error assigning load: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/make-call", tags=["AI Calls"], summary="Initiate AI Voice Call")
async def make_call(request: MakeCallRequest):
    """Initiate outbound call to a driver"""
    try:
        # Get driver info
        driver = db.get_driver_by_id(request.driver_id)
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Make call via Vapi
        call_response = await vapi_handler.create_outbound_call(
            driver['phone'],
            driver['name'],
            driver['id']
        )
        
        return {
            "success": True,
            "message": f"Call initiated to {driver['name']}",
            "call_id": call_response.get('id'),
            "driver": {
                "name": driver['name'],
                "phone": driver['phone']
            }
        }
    except ValueError as e:
        # Handle phone number validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error making call: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

# Add multiple HTTP methods for webhook validation
@app.get("/api/vapi/webhook")
@app.head("/api/vapi/webhook")
@app.options("/api/vapi/webhook")
def webhook_health():
    """Vapi webhook health check - supports GET, HEAD, OPTIONS"""
    return {"status": "ok", "message": "Webhook endpoint is ready"}

@app.post("/api/vapi/webhook")
async def vapi_webhook(request: Request):
    """Handle Vapi webhooks for call events"""
    try:
        # Handle OPTIONS preflight
        if request.method == "OPTIONS":
            return {"status": "ok"}
            
        body = await request.json()
        event_type = body.get("message", {}).get("type") or body.get("type")
        
        print(f"📥 Webhook received: {event_type}")
        
        # Handle function call event (both formats)
        if event_type in ["function-call", "tool-calls"]:
            print(f"📞 Processing {event_type} from AI")
            
            # Handle both old and new webhook formats
            if event_type == "tool-calls":
                tool_calls = body.get("message", {}).get("toolCalls", [])
                if tool_calls:
                    func_call = tool_calls[0].get("function", {})
                    func_call["name"] = func_call.get("name")
                    func_call["parameters"] = func_call.get("arguments", {})
                else:
                    func_call = {}
            else:
                func_call = body.get("message", {}).get("functionCall", {})
            
            if func_call.get("name") in ["update_driver_status", "updateLoadStatus", "updateLoadAssignment"]:
                params = func_call.get("parameters", {})
                
                # Get driver from call metadata or phone
                call_data = body.get("call", {})
                driver_id = call_data.get("metadata", {}).get("driver_id") if call_data else None
                
                if not driver_id:
                    # Try different locations for phone number
                    phone = None
                    
                    # Try in message.customer
                    if not phone:
                        phone = body.get("message", {}).get("customer", {}).get("number")
                    
                    # Try in message.phoneNumber
                    if not phone:
                        phone = body.get("message", {}).get("phoneNumber", {}).get("number")
                    
                    print(f"📞 Looking up driver: {phone}")
                    if phone:
                        # Try exact match first
                        driver = db.get_driver_by_phone(phone)
                        
                        # If not found, try without country code
                        if not driver and phone.startswith('+91'):
                            phone_without_code = phone[3:]  # Remove +91
                            driver = db.get_driver_by_phone(phone_without_code)
                        
                        # If not found, try with +91 prefix
                        if not driver and not phone.startswith('+'):
                            phone_with_code = f"+91{phone}"
                            driver = db.get_driver_by_phone(phone_with_code)
                        
                        if driver:
                            driver_id = driver['id']
                            print(f"✅ Found driver: {driver['name']}")
                        else:
                            print(f"❌ No driver found with phone: {phone}")
                    else:
                        print(f"❌ No phone number found anywhere in webhook data")
                
                if driver_id:
                    # Handle load assignment responses
                    if func_call.get("name") == "updateLoadAssignment":
                        assignment_status = params.get('status', 'needs_discussion')
                        reason = params.get('reason', '')
                        estimated_pickup = params.get('estimated_pickup', '')
                        concerns = params.get('concerns', '')
                        
                        # Update load assignment status
                        call_metadata = call_data.get('metadata', {})
                        load_id = call_metadata.get('load_id')
                        
                        if load_id:
                            db.update_load_assignment_status(load_id, driver_id, assignment_status, reason, estimated_pickup, concerns)
                        
                        # Create call log for load assignment
                        db.create_load_assignment_log(driver_id, load_id, assignment_status, reason, concerns, call_data.get('id'))
                        
                        print(f"✅ Load assignment updated: {assignment_status}")
                        
                    # Handle regular status updates
                    elif func_call.get("name") == "updateLoadStatus":
                        status = params.get('status', 'Available')
                        is_loaded = status == "Loaded"
                        location = params.get('location', 'Unknown')
                        reason = params.get('reason', '')
                        
                        # Update driver status
                        db.update_driver_status(driver_id, is_loaded, location, reason)
                        
                        # Create call log
                        db.create_call_log(driver_id, is_loaded, reason, location, call_data.get('id'))
                        
                        status_text = "Loaded" if is_loaded else "Available"
                        print(f"✅ Updated driver status to: {status_text}")
                        
                    else:
                        # Handle old format
                        is_loaded = params.get('is_loaded', False)
                        location = params.get('location', 'Unknown')
                        reason = params.get('reason_not_loaded', '')
                        
                        # Update driver status
                        db.update_driver_status(driver_id, is_loaded, location, reason)
                        
                        # Create call log
                        db.create_call_log(driver_id, is_loaded, reason, location, call_data.get('id'))
                        
                        status_text = "Loaded" if is_loaded else "Available"
                        print(f"✅ Updated driver status to: {status_text}")
                else:
                    print(f"❌ Driver not found")
        
        # Handle call end event
        elif event_type == "end-of-call-report":
            print("✅ Call ended, report received")
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Webhook error: {e}", file=sys.stderr)
        return {"status": "error", "message": str(e)}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "Hemut Voice AI",
        "version": "1.0.0",
        "port": os.getenv("PORT", "8000"),
        "features": ["AI Voice Calls", "Real-time Updates", "International Support"]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)