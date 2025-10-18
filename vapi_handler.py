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

async def create_outbound_call(driver_phone: str, driver_name: str, driver_id: str):
    """Create outbound call to driver via Vapi"""
    

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use custom Twilio if available, otherwise use Vapi number
    payload = {
        "customer": {
            "number": driver_phone,
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
    
    # Use the correct Twilio phone number ID
    payload["phoneNumberId"] = "5a59919f-b236-4e3e-af19-d61fb1791e8c"
    print(f" Making call to: {driver_phone}")
    
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
