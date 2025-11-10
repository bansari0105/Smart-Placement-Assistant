from flask import Blueprint, jsonify, request
from app.services.firebase_service import get_db, token_required
from app.services.chatbot_engine import ChatbotEngine
from app.services.scraper_company import CompanyScraper
from firebase_admin import firestore
import logging

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat_bp", __name__)

@chat_bp.route("/messages", methods=["GET"])
@token_required
def get_messages():
    """Get chat messages for the authenticated user"""
    try:
        uid = request.user["uid"]
        db = get_db()
        
        # Get messages where user is sender or receiver
        # Using 'chats' collection as per Firebase schema
        sent_messages = db.collection("chats").where("senderId", "==", uid).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).get()
        received_messages = db.collection("chats").where("receiverId", "==", uid).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).get()
        
        messages = []
        message_ids = set()
        
        # Add sent messages
        for msg_doc in sent_messages:
            msg_data = msg_doc.to_dict()
            msg_data["id"] = msg_doc.id
            if "timestamp" in msg_data:
                timestamp = msg_data["timestamp"]
                if hasattr(timestamp, "timestamp"):
                    msg_data["timestamp"] = timestamp.timestamp()
            messages.append(msg_data)
            message_ids.add(msg_doc.id)
        
        # Add received messages (avoid duplicates)
        for msg_doc in received_messages:
            if msg_doc.id not in message_ids:
                msg_data = msg_doc.to_dict()
                msg_data["id"] = msg_doc.id
                if "timestamp" in msg_data:
                    timestamp = msg_data["timestamp"]
                    if hasattr(timestamp, "timestamp"):
                        msg_data["timestamp"] = timestamp.timestamp()
                messages.append(msg_data)
        
        # Sort by timestamp
        messages.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        messages = messages[:50]  # Limit to 50 most recent
        
        messages.reverse()  # Show oldest first
        return jsonify({"messages": messages}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/messages", methods=["POST"])
@token_required
def send_message():
    """Send a chat message"""
    try:
        uid = request.user["uid"]
        data = request.get_json() or {}
        
        message_text = data.get("message") or data.get("text")
        receiver_id = data.get("receiverId")
        
        if not message_text:
            return jsonify({"error": "Missing message text"}), 400
        
        # If no receiverId, it's a global chat (use a default receiver or allow null)
        # For now, we'll require receiverId for one-on-one chat
        # You can modify this for global chat
        
        db = get_db()
        message_data = {
            "senderId": uid,
            "receiverId": receiver_id or "global",  # Use "global" for public chat
            "message": message_text,
            "isRead": False,
            "timestamp": firestore.SERVER_TIMESTAMP,
        }
        doc_ref = db.collection("chats").document()
        doc_ref.set(message_data)
        
        message_data["id"] = doc_ref.id
        return jsonify({"message": "Message sent", "message_data": message_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/messages/<message_id>/read", methods=["PUT"])
@token_required
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        uid = request.user["uid"]
        db = get_db()
        message_ref = db.collection("chats").document(message_id)
        message_doc = message_ref.get()
        
        if not message_doc.exists:
            return jsonify({"error": "Message not found"}), 404
        
        message_data = message_doc.to_dict()
        # Only mark as read if user is the receiver
        if message_data.get("receiverId") != uid:
            return jsonify({"error": "Unauthorized"}), 403
        
        message_ref.update({"isRead": True})
        return jsonify({"message": "Message marked as read"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/smart-query", methods=["POST"])
@token_required
def smart_query():
    """
    Smart query endpoint - automatically scrapes ANY company name.
    Same as /chatbot/smart-query but under /chat route.
    
    Request JSON:
    {
        "userMessage": "what is meril?"
    }
    
    Response:
    {
        "companyName": "Meril",
        "source": "scraped" | "knowledge_base",
        "data": {
            "description": "...",
            "skills": [...],
            "eligibility": "...",
            "process": "...",
            "salary": "..."
        },
        "response": "<formatted answer>"
    }
    """
    try:
        uid = request.user["uid"]
        data = request.get_json() or {}
        
        user_message = data.get("userMessage", "").strip()
        userId = data.get("userId") or uid
        
        if not user_message:
            return jsonify({"error": "Missing userMessage"}), 400
        
        db = get_db()
        engine = ChatbotEngine(db)
        
        # Extract company name from message
        company_name = engine.extract_company_name(user_message)
        
        if not company_name:
            return jsonify({
                "error": "Could not extract company name from message",
                "response": "Please mention a company name. For example: 'What is Meril?' or 'Tell me about Deloitte'"
            }), 400
        
        logger.info(f"Extracted company name: {company_name}")
        
        # Check knowledge base first
        knowledge = engine.search_knowledge_base(user_message, company_name)
        
        if knowledge:
            # Return from knowledge base
            return jsonify({
                "companyName": company_name,
                "source": "knowledge_base",
                "data": {
                    "description": knowledge.get('description', ''),
                    "skills": knowledge.get('skills', []),
                    "eligibility": knowledge.get('eligibility', ''),
                    "process": knowledge.get('process', ''),
                    "salary": knowledge.get('salary', ''),
                },
                "response": engine.generate_response_from_knowledge(
                    engine.classify_intent(user_message)[0],
                    knowledge,
                    user_message
                )
            }), 200
        
        # Not in knowledge base - trigger scraping
        logger.info(f"Company {company_name} not in knowledge base. Triggering scraping...")
        
        try:
            # Use dedicated CompanyScraper
            optional_url = None
            try:
                companies = db.collection('companies').where(
                    'company_name', '==', company_name
                ).limit(1).get()
                if companies:
                    optional_url = companies[0].to_dict().get('optional_url')
            except Exception as e:
                logger.debug(f"Could not get optional URL: {e}")
            
            company_scraper = CompanyScraper(db)
            
            # Scrape company using dedicated scraper
            scraped_data = company_scraper.scrape_company(company_name, optional_url)
            
            # Save to Firestore automatically (only if data quality is good)
            save_success = company_scraper.save_to_firestore(company_name, scraped_data)
            if not save_success:
                logger.warning(f"Did not save {company_name} to knowledge base - data quality too low")
            
            # Generate formatted response
            intent, _ = engine.classify_intent(user_message)
            formatted_response = engine.generate_response_from_knowledge(
                intent,
                scraped_data,
                user_message
            )
            
            # Save chat log
            engine.save_chat_log(
                userId,
                user_message,
                formatted_response,
                {
                    'intent': intent,
                    'company_name': company_name,
                    'source': 'scraped',
                }
            )
            
            return jsonify({
                "companyName": company_name,
                "source": "scraped",
                "data": {
                    "description": scraped_data.get('description', ''),
                    "skills": scraped_data.get('skills', []),
                    "eligibility": scraped_data.get('eligibility', ''),
                    "process": scraped_data.get('process', ''),
                    "salary": scraped_data.get('salary', ''),
                },
                "response": formatted_response
            }), 200
            
        except Exception as e:
            logger.error(f"Error during scraping for {company_name}: {e}")
            return jsonify({
                "error": f"Failed to scrape information for {company_name}",
                "companyName": company_name,
                "source": "error",
                "response": f"I encountered an error while gathering information about {company_name}. Please try again later."
            }), 500
        
    except Exception as e:
        logger.error(f"Error in smart_query: {e}")
        return jsonify({
            "error": str(e),
            "response": "I apologize, but I encountered an error. Please try again."
        }), 500
