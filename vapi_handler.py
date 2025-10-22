import httpx
import os
import asyncio
import random
from dotenv import load_dotenv
import database as db

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER")
VAPI_BASE_URL = "https://api.vapi.ai"

# Twilio credentials for international calls
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Validate required environment variables
if not VAPI_API_KEY:
    print("❌ Warning: VAPI_API_KEY not set")

if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER) and not VAPI_PHONE_NUMBER_ID:
    print("❌ Warning: Neither Twilio credentials nor Vapi phone number ID configured")

async def create_load_assignment_call(driver_phone: str, driver_name: str, driver_id: str, load: dict):
    """Create outbound call to driver for load assignment"""
    
    # Format phone number properly for Indian numbers
    formatted_phone = format_indian_phone_number(driver_phone)
    print(f"📞 Formatted phone for load assignment: {driver_phone} -> {formatted_phone}")
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Create detailed load information
    load_details = f"Load {load.get('load_number', 'N/A')} from {load.get('pickup_location', 'pickup location')} to {load.get('delivery_location', 'delivery location')}, weight {load.get('weight', 'unknown')} lbs"
    
    payload = {
        "customer": {
            "number": formatted_phone,
            "name": driver_name
        },
        "assistantId": None,
        "assistant": {
            "firstMessage": f"Hi {driver_name}, this is Hemut AI. I have a new load assignment for you: {load_details}. Can you confirm if you can take this load?",
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": f"""You are a friendly dispatch assistant for Hemut trucking company. You're calling {driver_name} about a load assignment.

LOAD DETAILS:
- Load Number: {load.get('load_number', 'N/A')}
- Pickup: {load.get('pickup_location', 'Unknown')}
- Delivery: {load.get('delivery_location', 'Unknown')}
- Weight: {load.get('weight', 'Unknown')} lbs

YOUR CONVERSATION FLOW:
1. Start by confirming the load assignment details
2. Ask if they can accept this load
3. If YES: Ask about estimated pickup time and any concerns
4. If NO: Ask for the reason and when they might be available
5. Be conversational - they can ask about weather, road conditions, or other concerns
6. Keep the conversation natural and helpful
7. End by calling the updateLoadAssignment function with their response

IMPORTANT: Be conversational and helpful. Let them talk about weather, road conditions, or any concerns they have. This should feel like talking to a real dispatcher."""
                    }
                ],
                "functions": [
                    {
                        "name": "updateLoadAssignment",
                        "description": "Update the load assignment status based on driver response",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "status": {
                                    "type": "string",
                                    "enum": ["accepted", "rejected", "needs_discussion"],
                                    "description": "Driver's response to the load assignment"
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "Driver's reason or additional comments"
                                },
                                "estimated_pickup": {
                                    "type": "string",
                                    "description": "Driver's estimated pickup time if accepted"
                                },
                                "concerns": {
                                    "type": "string",
                                    "description": "Any concerns about weather, road conditions, etc."
                                }
                            },
                            "required": ["status", "reason"]
                        }
                    }
                ]
            },
            "voice": {
                "voiceId": "Elliot",
                "provider": "vapi"
            },
            "recordingEnabled": True,
            "endCallMessage": "Thank you! I'll update the system with your response. Drive safe!",
            "endCallFunctionEnabled": True,
            "metadata": {
                "driver_id": driver_id,
                "load_id": load.get('id'),
                "call_type": "load_assignment"
            }
        }
    }
    
    # Configure Twilio for Indian numbers if credentials are available
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        payload["phoneNumber"] = {
            "twilioAccountSid": TWILIO_ACCOUNT_SID,
            "twilioAuthToken": TWILIO_AUTH_TOKEN,
            "number": TWILIO_PHONE_NUMBER
        }
        print(f"📞 Using Twilio configuration for load assignment call")
    elif VAPI_PHONE_NUMBER_ID:
        payload["phoneNumberId"] = VAPI_PHONE_NUMBER_ID
        print(f"📞 Using Vapi phone number ID for load assignment")
    else:
        print(f"❌ No phone number configuration found")
        raise ValueError("No phone number configuration available")
    
    print(f"📞 Making load assignment call to: {formatted_phone}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VAPI_BASE_URL}/call/phone",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 201:
                print(f"✅ Load assignment call initiated successfully")
            else:
                print(f"❌ Call failed: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"❌ Call Error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"❌ Response status: {e.response.status_code}")
                print(f"❌ Response body: {e.response.text}")
            raise

def format_indian_phone_number(phone: str) -> str:
    """Format phone number for Indian numbers with proper E.164 format"""
    # Remove any spaces, dashes, or other characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Handle different Indian number formats
    if phone.startswith('91') and len(phone) == 12:
        return f"+{phone}"
    elif len(phone) == 10:
        return f"+91{phone}"
    elif phone.startswith('0') and len(phone) == 11:
        return f"+91{phone[1:]}"
    else:
        # Return as is with + if it looks like it already has country code
        return f"+{phone}" if not phone.startswith('+') else phone

async def create_outbound_call(driver_phone: str, driver_name: str, driver_id: str):
    """Create outbound call to driver via Vapi"""
    
    # Format phone number properly for Indian numbers
    formatted_phone = format_indian_phone_number(driver_phone)
    print(f"📞 Formatted phone: {driver_phone} -> {formatted_phone}")

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use custom Twilio if available, otherwise use Vapi number
    payload = {
        "customer": {
            "number": formatted_phone,
            "name": driver_name
        },
        "assistantId": None,  # We'll use inline assistant
        "assistant": {
            "firstMessage": f"Hi {driver_name}, this is Hemut AI calling to check on your load status. Have you successfully picked it up?",
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an automated dispatch assistant for a trucking company named Hemut. You are friendly, professional, and efficient. Your tone should be clear and direct.\n\nYour primary goal is to confirm the pickup status of a load from a truck driver.\n\nYour instructions are:\n1. The call will start with a pre-defined first message that includes the driver's name and asks about pickup status.\n2. Your first task is to listen to the driver's response to the question: \"Have you successfully picked it up?\"\n3. If the driver says \"yes,\" \"confirmed,\" or any positive affirmation, your job is complete. Call the `updateLoadStatus` function with the `status` parameter set to \"Loaded\" and the `reason` parameter as an empty string. Then, say \"Thank you for confirming. Goodbye.\" and end the call.\n4. If the driver says \"no,\" \"not yet,\" or any negative response, you must ask one follow-up question: \"Okay, can you please tell me the reason for the delay?\"\n5. After they give you the reason, call the `updateLoadStatus` function with the `status` parameter set to \"Delayed\" and the `reason` parameter set to whatever the driver told you. Then, say \"I've noted that down. Thank you. Goodbye.\" and end the call.\n\nDo not engage in small talk or answer questions outside of this mission. Your only purpose is to get the load status and the reason for any delay."
                    }
                ],
                "functions": [
                    {
                        "name": "updateLoadStatus",
                        "description": "Update driver's load status and location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "status": {
                                    "type": "string",
                                    "enum": ["Loaded", "Delayed", "Available"],
                                    "description": "Current status of the driver - Loaded if picked up, Delayed if not picked up"
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "Reason for delay if status is Delayed, empty string if Loaded"
                                },
                                "location": {
                                    "type": "string",
                                    "description": "Driver's current location or destination"
                                }
                            },
                            "required": ["status", "reason"]
                        }
                    }
                ]
            },
            "voice": {
                "voiceId": "Elliot",
                "provider": "vapi"
            },
            "recordingEnabled": True,
            "endCallMessage": "Goodbye.",
            "endCallFunctionEnabled": True,
            "metadata": {
                "driver_id": driver_id
            }
        }
    }
    
    # Configure Twilio for Indian numbers if credentials are available
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        payload["phoneNumber"] = {
            "twilioAccountSid": TWILIO_ACCOUNT_SID,
            "twilioAuthToken": TWILIO_AUTH_TOKEN,
            "number": TWILIO_PHONE_NUMBER
        }
        print(f"📞 Using Twilio configuration for call")
    elif VAPI_PHONE_NUMBER_ID:
        payload["phoneNumberId"] = VAPI_PHONE_NUMBER_ID
        print(f"📞 Using Vapi phone number ID")
    else:
        print(f"❌ No phone number configuration found")
        raise ValueError("No phone number configuration available")
    
    print(f"📞 Making call to: {formatted_phone}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VAPI_BASE_URL}/call/phone",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 201:
                print(f"Call initiated successfully")
            else:
                print(f"Call failed: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"âŒ Call Error: {e}")
            raise

async def simulate_webhook_callback(driver_id: str, driver_name: str):
    """Simulate a webhook callback for testing purposes"""
    await asyncio.sleep(5)  # Wait 5 seconds to simulate call duration
    
    # Generate random realistic responses
    scenarios = [
        {"is_loaded": True, "location": "Dallas, TX", "reason": None},
        {"is_loaded": True, "location": "Chicago, IL", "reason": None},
        {"is_loaded": False, "location": "Atlanta, GA", "reason": "waiting for assignment"},
        {"is_loaded": False, "location": "Phoenix, AZ", "reason": "maintenance"},
        {"is_loaded": False, "location": "Miami, FL", "reason": "home time"},
    ]
    
    scenario = random.choice(scenarios)
    
    print(f"SIMULATING: Driver {driver_name} callback - Loaded: {scenario['is_loaded']}, Location: {scenario['location']}")
    
    # Update database just like a real webhook would
    db.update_driver_status(
        driver_id,
        scenario['is_loaded'],
        scenario['location'],
        scenario['reason']
    )
    
    # Create call log
    db.create_call_log(
        driver_id,
        scenario['is_loaded'],
        scenario['reason'],
        scenario['location'],
        f"test_call_{driver_id}"
    )
    
    print(f"SIMULATION COMPLETE: Updated driver {driver_id} status")
