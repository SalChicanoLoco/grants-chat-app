import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('CONVERSATIONS_TABLE', 'GrantsConversations')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function to handle chat requests for Grants Assistant
    """
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        user_message = body.get('message', '')
        conversation_id = body.get('conversationId') or str(uuid.uuid4())
        
        if not user_message:
            return error_response('Message is required', 400)
        
        # Store user message in DynamoDB
        timestamp = datetime.utcnow().isoformat() + 'Z'
        store_message(conversation_id, 'user', user_message, timestamp)
        
        # Generate AI response (for now, use simple logic - replace with actual AI later)
        ai_response = generate_response(user_message)
        
        # Store AI response in DynamoDB
        response_timestamp = datetime.utcnow().isoformat() + 'Z'
        store_message(conversation_id, 'assistant', ai_response, response_timestamp)
        
        # Return response
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': ai_response,
                'conversationId': conversation_id,
                'timestamp': response_timestamp
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(f"Internal server error: {str(e)}", 500)

def store_message(conversation_id, sender, message, timestamp):
    """Store a message in DynamoDB with TTL for automatic cleanup"""
    try:
        # Set TTL to 30 days from now (for free tier storage management)
        ttl = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        
        table.put_item(
            Item={
                'conversationId': conversation_id,
                'timestamp': timestamp,
                'sender': sender,
                'message': message,
                'messageId': str(uuid.uuid4()),
                'ttl': ttl  # DynamoDB will auto-delete after this timestamp
            }
        )
    except Exception as e:
        print(f"Error storing message: {str(e)}")
        raise

def generate_response(user_message):
    """
    Generate AI response based on user message
    TODO: Replace with actual AI/LLM integration (OpenAI, Bedrock, etc.)
    """
    message_lower = user_message.lower()
    
    # Simple pattern matching for demo
    if 'grant' in message_lower and 'write' in message_lower:
        return "I can help you write grants! A strong grant proposal typically includes: 1) Executive Summary, 2) Statement of Need, 3) Project Description, 4) Budget, and 5) Organization Information. What specific aspect would you like help with?"
    
    elif 'budget' in message_lower:
        return "For grant budgets, make sure to include: personnel costs, equipment, supplies, travel, and indirect costs. Be realistic and justify each expense clearly. Would you like me to help you create a budget template?"
    
    elif 'deadline' in message_lower or 'timeline' in message_lower:
        return "Managing grant deadlines is crucial! I recommend creating a timeline that works backwards from the submission date, allowing time for reviews, revisions, and gathering required documents. Would you like help planning your timeline?"
    
    elif 'hello' in message_lower or 'hi' in message_lower:
        return "Hello! I'm here to help you with grant writing and applications. Feel free to ask me about proposal structure, budgets, timelines, or any other grant-related questions."
    
    else:
        return "Thank you for your question. I'm here to help with grant writing, applications, budgets, timelines, and proposal development. Could you provide more details about what you need help with?"

def get_cors_headers():
    """Return CORS headers for API Gateway"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'OPTIONS,POST',
        'Content-Type': 'application/json'
    }

def error_response(message, status_code):
    """Return an error response"""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'error': message
        })
    }
