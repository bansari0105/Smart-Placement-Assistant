import 'dart:async';
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../services/firebase_service.dart';
import '../services/backend_api_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final FirebaseService _firebaseService = FirebaseService();
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isSending = false;
  bool _isBotResponding = false;
  bool _isScraping = false;
  String? _scrapingCompanyName;
  List<Map<String, dynamic>> _chatHistory = [];

  @override
  void initState() {
    super.initState();
    _loadChatHistory();
  }

  Future<void> _loadChatHistory() async {
    try {
      final history = await BackendApiService.getChatHistory(limit: 20);
      setState(() {
        _chatHistory = history;
      });
    } catch (e) {
      print('Error loading chat history: $e');
    }
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _isSending || _isBotResponding) return;

    setState(() {
      _isSending = true;
      _isBotResponding = true;
    });

    // Store message before clearing (for fallback)
    final userMessage = text;
    
    try {
      final userId = _firebaseService.getCurrentUserId();
      if (userId == null) {
        throw Exception('User not authenticated');
      }

      // Save user message to Firestore for display
      await _firebaseService.sendChatMessage(text, receiverId: 'chatbot');
      
      // Clear input
      _messageController.clear();

      // Use smart query for automatic company scraping
      Map<String, dynamic>? response;
      
      // Check if this might be a company query
      final mightBeCompany = _mightBeCompanyQuery(text);
      if (mightBeCompany) {
        setState(() {
          _isScraping = true;
          _scrapingCompanyName = _extractPotentialCompanyName(text);
        });
      }
      
      try {
        response = await BackendApiService.smartQuery(text, userId: userId)
            .timeout(
              const Duration(seconds: 45), // Longer timeout for scraping
              onTimeout: () {
                throw TimeoutException('Request timed out. Scraping may take longer. Please try again.');
              },
            );
      } catch (e) {
        // If backend is unavailable, provide fallback response
        if (e.toString().contains('Failed host lookup') || 
            e.toString().contains('Connection refused') ||
            e.toString().contains('timeout')) {
          final fallbackResponse = _getFallbackResponse(text);
          
          // Save fallback response
          final user = _firebaseService.getCurrentUser();
          if (user != null) {
            await FirebaseFirestore.instance.collection('chats').add({
              'senderId': 'chatbot',
              'receiverId': user.uid,
              'message': fallbackResponse,
              'isRead': false,
              'source': 'ai',
              'timestamp': FieldValue.serverTimestamp(),
            });
          }
          
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('⚠️ Backend not available. Using fallback response. Please start the backend server.'),
                duration: Duration(seconds: 4),
                backgroundColor: Colors.orange,
              ),
            );
          }
          
          setState(() {
            _isSending = false;
            _isBotResponding = false;
          });
          return;
        }
        rethrow;
      }

      if (response != null) {
        // Handle smart query response
        final botResponse = response['response'] as String? ?? 
                           response['error'] as String? ?? 
                           'I apologize, but I could not generate a response.';
        final source = response['source'] as String? ?? 'ai';
        final companyName = response['companyName'] as String?;
        final data = response['data'] as Map<String, dynamic>?;

        // Save bot response to Firestore (as if chatbot sent it)
        final user = _firebaseService.getCurrentUser();
        if (user != null) {
          await FirebaseFirestore.instance.collection('chats').add({
            'senderId': 'chatbot',
            'receiverId': user.uid,
            'message': botResponse,
            'isRead': false,
            'source': source,
            'companyName': companyName,
            'data': data,
            'timestamp': FieldValue.serverTimestamp(),
          });
        }
        
        // Add to local history
        setState(() {
          _chatHistory.add({
            'message': text,
            'response': botResponse,
            'source': source,
            'companyName': companyName,
            'data': data,
            'timestamp': DateTime.now(),
          });
        });

        // Clear scraping state
        setState(() {
          _isScraping = false;
          _scrapingCompanyName = null;
        });

        // Show source indicator
        if (mounted) {
          if (source == 'scraped') {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('✅ Information about ${companyName ?? "company"} scraped from latest sources'),
                duration: const Duration(seconds: 3),
                backgroundColor: Colors.green,
              ),
            );
          } else if (source == 'knowledge_base') {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('📚 Information about ${companyName ?? "company"} from knowledge base'),
                duration: const Duration(seconds: 2),
                backgroundColor: Colors.blue,
              ),
            );
          }
        }
      } else {
        throw Exception('No response from chatbot');
      }

      Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
    } catch (e) {
      print('Chatbot error: $e');
      if (mounted) {
        // Show error message
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to get response: ${e.toString()}'),
            duration: const Duration(seconds: 4),
            backgroundColor: Colors.red,
            action: SnackBarAction(
              label: 'Retry',
              textColor: Colors.white,
              onPressed: () => _sendMessage(),
            ),
          ),
        );
        
        // Provide fallback response (use stored message)
        final fallbackResponse = _getFallbackResponse(userMessage);
        final user = _firebaseService.getCurrentUser();
        if (user != null) {
          try {
            await FirebaseFirestore.instance.collection('chats').add({
              'senderId': 'chatbot',
              'receiverId': user.uid,
              'message': fallbackResponse,
              'isRead': false,
              'source': 'ai',
              'timestamp': FieldValue.serverTimestamp(),
            });
          } catch (e2) {
            print('Error saving fallback: $e2');
          }
        }
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
          _isBotResponding = false;
          _isScraping = false;
          _scrapingCompanyName = null;
        });
      }
    }
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("AI Interview Assistant"),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text("AI Interview Assistant"),
                  content: const Text(
                    "I'm your intelligent placement assistant powered by AI, NLP, and web scraping!\n\n"
                    "I can help you with:\n"
                    "• Company information and requirements\n"
                    "• Skills needed for placements\n"
                    "• Interview preparation tips\n"
                    "• Eligibility criteria\n"
                    "• Salary packages\n"
                    "• Placement drive details\n"
                    "• Resume guidance\n"
                    "• Learning roadmaps\n\n"
                    "I automatically search and learn from multiple sources to give you the most accurate answers!",
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Got it'),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Messages List
          Expanded(
            child: StreamBuilder<List<Map<String, dynamic>>>(
              stream: _firebaseService.getChatMessagesStream(),
              builder: (context, snapshot) {
                if (snapshot.hasError) {
                  return Center(
                    child: Text('Error: ${snapshot.error}'),
                  );
                }

                if (!snapshot.hasData) {
                  return const Center(
                    child: CircularProgressIndicator(),
                  );
                }

                final messages = snapshot.data!;
                
                // Filter to show only chatbot conversation
                final chatbotMessages = messages.where((msg) {
                  final senderId = msg['senderId'];
                  final receiverId = msg['receiverId'];
                  final userId = _firebaseService.getCurrentUserId();
                  return (senderId == userId && receiverId == 'chatbot') ||
                         (senderId == 'chatbot' && receiverId == userId);
                }).toList();

                if (chatbotMessages.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.smart_toy, size: 64, color: Colors.blue),
                        const SizedBox(height: 16),
                        const Text(
                          'Start chatting with your AI Interview Assistant!',
                          style: TextStyle(color: Colors.grey, fontSize: 16),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 32),
                          child: Text(
                            'Try asking:\n• "What skills does TCS need?"\n• "Tell me about Google"\n• "TCS interview process"\n• "How to prepare for technical interview"',
                            style: TextStyle(color: Colors.grey, fontSize: 14),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ],
                    ),
                  );
                }

                WidgetsBinding.instance.addPostFrameCallback((_) {
                  _scrollToBottom();
                });

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(12),
                  itemCount: chatbotMessages.length,
                  itemBuilder: (context, index) {
                    final message = chatbotMessages[index];
                    final senderId = message['senderId'];
                    final isBot = senderId == 'chatbot';
                    final isCurrentUser = senderId == _firebaseService.getCurrentUserId();

                    return Align(
                      alignment: isCurrentUser
                          ? Alignment.centerRight
                          : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: isBot
                              ? Colors.green.shade50
                              : isCurrentUser
                                  ? Colors.blue.shade100
                                  : Colors.grey.shade200,
                          borderRadius: BorderRadius.circular(12),
                          border: isBot
                              ? Border.all(color: Colors.green.shade200, width: 1)
                              : null,
                        ),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.75,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                if (isBot) ...[
                                  const Icon(Icons.smart_toy, size: 16, color: Colors.green),
                                  const SizedBox(width: 4),
                                ],
                                Text(
                                  isBot ? 'AI Assistant' : 'You',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12,
                                    color: isBot
                                        ? Colors.green.shade900
                                        : Colors.blue.shade900,
                                  ),
                                ),
                                if (isBot && message['source'] != null) ...[
                                  const SizedBox(width: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: _getSourceColor(message['source']),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      _getSourceLabel(message['source']),
                                      style: TextStyle(
                                        fontSize: 9,
                                        color: _getSourceTextColor(message['source']),
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ],
                                if (isBot && message['companyName'] != null) ...[
                                  const SizedBox(width: 4),
                                  Text(
                                    '• ${message['companyName']}',
                                    style: TextStyle(
                                      fontSize: 10,
                                      color: Colors.grey.shade600,
                                      fontStyle: FontStyle.italic,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(
                              message['message'] ?? '',
                              style: const TextStyle(fontSize: 14),
                            ),
                            if (message['timestamp'] != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Text(
                                  _formatTimestamp(message['timestamp']),
                                  style: TextStyle(
                                    fontSize: 10,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),

          // Typing/Scraping indicator
          if (_isBotResponding)
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: _isScraping ? Colors.orange.shade50 : Colors.grey.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: _isScraping ? Colors.orange.shade200 : Colors.grey.shade300,
                  width: 1,
                ),
              ),
              child: Row(
                children: [
                  const SizedBox(width: 8),
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        _isScraping ? Colors.orange.shade600 : Colors.green.shade400,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _isScraping 
                            ? '🔍 Scraping data...' 
                            : 'AI Assistant is thinking',
                          style: TextStyle(
                            color: _isScraping ? Colors.orange.shade900 : Colors.grey.shade700,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        if (_isScraping && _scrapingCompanyName != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            'Gathering information about $_scrapingCompanyName',
                            style: TextStyle(
                              color: Colors.orange.shade700,
                              fontSize: 11,
                            ),
                          ),
                        ],
                        if (_isScraping) ...[
                          const SizedBox(height: 4),
                          Text(
                            'This may take a few moments',
                            style: TextStyle(
                              color: Colors.orange.shade600,
                              fontSize: 10,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),

          // Message Input
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.shade300,
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: InputDecoration(
                      hintText: 'Ask about companies, skills, interviews...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                    enabled: !_isSending && !_isBotResponding,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: (_isSending || _isBotResponding) ? null : _sendMessage,
                  icon: _isSending
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send, color: Colors.blue),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getSourceLabel(String? source) {
    switch (source) {
      case 'firestore':
      case 'knowledge_base':
        return '📚 KNOWLEDGE BASE';
      case 'scraped':
        return '🔍 LIVE DATA';
      case 'ai':
        return '🤖 AI GENERATED';
      default:
        return '🤖 AI';
    }
  }

  Color _getSourceColor(String? source) {
    switch (source) {
      case 'firestore':
      case 'knowledge_base':
        return Colors.blue.shade100;
      case 'scraped':
        return Colors.green.shade100;
      case 'ai':
        return Colors.purple.shade100;
      default:
        return Colors.grey.shade100;
    }
  }

  Color _getSourceTextColor(String? source) {
    switch (source) {
      case 'firestore':
      case 'knowledge_base':
        return Colors.blue.shade900;
      case 'scraped':
        return Colors.green.shade900;
      case 'ai':
        return Colors.purple.shade900;
      default:
        return Colors.grey.shade900;
    }
  }

  String _formatTimestamp(dynamic timestamp) {
    if (timestamp == null) return '';
    try {
      DateTime dateTime;
      if (timestamp is DateTime) {
        dateTime = timestamp;
      } else {
        return '';
      }

      final now = DateTime.now();
      final difference = now.difference(dateTime);

      if (difference.inMinutes < 1) {
        return 'Just now';
      } else if (difference.inHours < 1) {
        return '${difference.inMinutes}m ago';
      } else if (difference.inDays < 1) {
        return '${difference.inHours}h ago';
      } else {
        return '${dateTime.day}/${dateTime.month} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
      }
    } catch (e) {
      return '';
    }
  }

  /// Fallback response when backend is unavailable
  String _getFallbackResponse(String query) {
    final queryLower = query.toLowerCase();
    
    if (queryLower.contains('hello') || queryLower.contains('hi') || queryLower.contains('hey')) {
      return "Hello! 👋 I'm your AI Interview Assistant.\n\n"
          "⚠️ **Backend Connection Issue:**\n"
          "The backend server is not available right now. Please:\n\n"
          "1. Start the backend server:\n"
          "   ```bash\n"
          "   cd lib/backend\n"
          "   python -m app.main\n"
          "   ```\n\n"
          "2. Make sure it's running on http://localhost:5000\n\n"
          "For now, I can still help with basic questions! What would you like to know?";
    }
    
    if (queryLower.contains('tcs') || queryLower.contains('tata')) {
      return "**About TCS (Tata Consultancy Services):**\n\n"
          "TCS is one of India's largest IT services companies.\n\n"
          "**Common Skills Required:**\n"
          "• Java, Python, C++\n"
          "• Data Structures & Algorithms\n"
          "• SQL, Database Management\n"
          "• Problem-solving skills\n\n"
          "**Note:** For detailed, up-to-date information, please start the backend server to enable web scraping.";
    }
    
    if (queryLower.contains('zomato')) {
      return "**About Zomato:**\n\n"
          "Zomato is a food delivery and restaurant discovery platform.\n\n"
          "**Tech Stack:**\n"
          "• Python, Django\n"
          "• React, JavaScript\n"
          "• AWS, Cloud Services\n"
          "• Mobile Development (iOS/Android)\n\n"
          "**Note:** For detailed, up-to-date information, please start the backend server.";
    }
    
    if (queryLower.contains('skill')) {
      return "**Essential Skills for Placements:**\n\n"
          "🔧 **Technical Skills:**\n"
          "• Programming Languages (Java, Python, C++)\n"
          "• Data Structures & Algorithms\n"
          "• Database (SQL, MongoDB)\n"
          "• System Design basics\n\n"
          "💼 **Soft Skills:**\n"
          "• Communication\n"
          "• Problem-solving\n"
          "• Teamwork\n\n"
          "**Note:** For company-specific skills, please start the backend server.";
    }
    
    return "I understand you're asking: \"$query\"\n\n"
        "⚠️ **Backend Not Available:**\n"
        "The AI backend server is not running. To get intelligent, scraped answers:\n\n"
        "1. Start backend: `cd lib/backend && python -m app.main`\n"
        "2. Make sure it's on http://localhost:5000\n\n"
        "**I can still help with:**\n"
        "• General interview tips\n"
        "• Basic company information\n"
        "• Resume guidance\n\n"
        "Try asking: \"What skills does TCS need?\" or \"Tell me about Google\"";
  }

  /// Check if query might be asking about a company
  bool _mightBeCompanyQuery(String query) {
    final lower = query.toLowerCase();
    final companyIndicators = [
      'what is', 'tell me about', 'about', 'company', 'skills', 
      'eligibility', 'process', 'interview', 'salary', 'package'
    ];
    return companyIndicators.any((indicator) => lower.contains(indicator));
  }

  /// Extract potential company name from query (simple heuristic)
  String? _extractPotentialCompanyName(String query) {
    // Find capitalized words
    final capitalized = RegExp(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b').allMatches(query);
    if (capitalized.isNotEmpty) {
      return capitalized.first.group(0);
    }
    // If no capitalized words, try extracting after common phrases
    final patterns = [
      RegExp(r'what\s+is\s+(\w+)', caseSensitive: false),
      RegExp(r'tell\s+me\s+about\s+(\w+)', caseSensitive: false),
      RegExp(r'about\s+(\w+)', caseSensitive: false),
    ];
    for (var pattern in patterns) {
      final match = pattern.firstMatch(query);
      if (match != null) {
        return match.group(1)?.toLowerCase().split(' ').map((w) => 
          w.isEmpty ? '' : w[0].toUpperCase() + w.substring(1)
        ).join(' ');
      }
    }
    return null;
  }
}
