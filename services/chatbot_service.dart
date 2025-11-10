import 'package:cloud_firestore/cloud_firestore.dart';
import 'firebase_service.dart';

class ChatbotService {
  final FirebaseService _firebaseService = FirebaseService();
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  /// Generate AI chatbot response for interview preparation
  Future<String> generateResponse(String userMessage, String userId) async {
    final message = userMessage.toLowerCase().trim();

    // Get user's applications for context
    List<Map<String, dynamic>> applications = [];
    try {
      final appsSnapshot = await _firestore
          .collection('applications')
          .where('userId', isEqualTo: userId)
          .where('status', isEqualTo: 'applied')
          .limit(5)
          .get();
      
      for (var doc in appsSnapshot.docs) {
        applications.add(doc.data());
      }
    } catch (e) {
      print('Error fetching applications: $e');
    }

    // Get company data for context
    Map<String, dynamic>? companyContext;
    if (applications.isNotEmpty) {
      final companyId = applications.first['companyId'];
      if (companyId != null) {
        try {
          companyContext = await _firebaseService.getScrapedCompany(companyId);
        } catch (e) {
          print('Error fetching company data: $e');
        }
      }
    }

    // Pattern matching for common interview questions
    if (message.contains('hello') || message.contains('hi') || message.contains('hey')) {
      return "Hello! 👋 I'm your Interview Preparation Assistant. I can help you with:\n\n"
          "• Interview tips and strategies\n"
          "• Skills preparation\n"
          "• Company-specific advice\n"
          "• Common interview questions\n"
          "• Technical interview preparation\n\n"
          "What would you like to know?";
    }

    if (message.contains('interview') && message.contains('tip')) {
      return "Here are some key interview tips:\n\n"
          "✅ **Before the Interview:**\n"
          "• Research the company thoroughly\n"
          "• Review the job description and requirements\n"
          "• Prepare questions to ask the interviewer\n"
          "• Practice common interview questions\n"
          "• Prepare examples using STAR method (Situation, Task, Action, Result)\n\n"
          "✅ **During the Interview:**\n"
          "• Arrive 10-15 minutes early\n"
          "• Dress professionally\n"
          "• Maintain eye contact and positive body language\n"
          "• Listen carefully and answer concisely\n"
          "• Ask thoughtful questions\n\n"
          "✅ **After the Interview:**\n"
          "• Send a thank-you email within 24 hours\n"
          "• Follow up if you don't hear back\n"
          "• Reflect on what went well and what to improve";
    }

    if (message.contains('technical') || message.contains('coding') || message.contains('dsa')) {
      final skills = companyContext?['skills'] as List<dynamic>?;
      final skillsList = skills?.take(5).map((s) => s.toString()).join(', ') ?? 'general programming';
      
      return "For technical interviews, focus on:\n\n"
          "📚 **Core Topics:**\n"
          "• Data Structures (Arrays, Linked Lists, Trees, Graphs, Hash Tables)\n"
          "• Algorithms (Sorting, Searching, Dynamic Programming)\n"
          "• Time & Space Complexity Analysis\n"
          "• Problem-solving patterns\n\n"
          "💻 **For your applications, focus on:** $skillsList\n\n"
          "🎯 **Practice Resources:**\n"
          "• LeetCode (start with easy, progress to medium)\n"
          "• HackerRank\n"
          "• CodeSignal\n"
          "• Practice explaining your thought process out loud\n\n"
          "💡 **Tips:**\n"
          "• Start by clarifying the problem\n"
          "• Think of edge cases\n"
          "• Explain your approach before coding\n"
          "• Write clean, readable code\n"
          "• Test your solution with examples";
    }

    if (message.contains('skill') || message.contains('learn') || message.contains('prepare')) {
      final skills = companyContext?['skills'] as List<dynamic>?;
      if (skills != null && skills.isNotEmpty) {
        final skillsList = skills.take(10).map((s) => s.toString()).join('\n• ');
        return "Based on your applications, here are key skills to focus on:\n\n"
            "🎯 **Priority Skills:**\n"
            "• $skillsList\n\n"
            "📖 **How to Learn:**\n"
            "• Build projects using these technologies\n"
            "• Practice coding problems\n"
            "• Read documentation and tutorials\n"
            "• Join online communities\n"
            "• Work on real-world projects\n\n"
            "💪 **Practice Daily:**\n"
            "• Set aside 1-2 hours daily for skill development\n"
            "• Focus on one skill at a time\n"
            "• Build a portfolio showcasing your skills";
      } else {
        return "Here are essential skills for placement interviews:\n\n"
            "🔧 **Technical Skills:**\n"
            "• Programming languages (Java, Python, C++)\n"
            "• Data Structures & Algorithms\n"
            "• Database (SQL, NoSQL)\n"
            "• System Design basics\n"
            "• Version Control (Git)\n\n"
            "💼 **Soft Skills:**\n"
            "• Communication\n"
            "• Problem-solving\n"
            "• Teamwork\n"
            "• Time management\n\n"
            "📚 **How to Prepare:**\n"
            "• Practice coding daily\n"
            "• Build projects\n"
            "• Participate in coding contests\n"
            "• Review computer science fundamentals";
      }
    }

    if (message.contains('company') || message.contains('applied')) {
      if (applications.isNotEmpty) {
        final companyNames = applications.map((app) => app['companyName'] ?? 'Company').join(', ');
        return "You've applied to: **$companyNames**\n\n"
            "🎯 **Next Steps:**\n"
            "• Research each company's interview process\n"
            "• Review company-specific requirements\n"
            "• Prepare company-specific questions\n"
            "• Check the Suggestions tab for personalized tips\n\n"
            "💡 **Pro Tip:** Use the company detail pages to see specific skills and requirements for each company you've applied to!";
      } else {
        return "You haven't applied to any companies yet. Here's how to get started:\n\n"
            "1. Go to the **Companies** tab\n"
            "2. Browse available companies\n"
            "3. Click on a company to see details\n"
            "4. Click **Apply Now** to submit your application\n\n"
            "Once you apply, I can give you personalized interview preparation advice!";
      }
    }

    if (message.contains('question') || message.contains('ask')) {
      return "Here are common interview questions and how to answer them:\n\n"
          "❓ **Tell me about yourself:**\n"
          "• Give a brief overview (30-60 seconds)\n"
          "• Focus on relevant experience and skills\n"
          "• Connect your background to the role\n\n"
          "❓ **Why do you want to work here?**\n"
          "• Show you've researched the company\n"
          "• Mention specific aspects that interest you\n"
          "• Connect your goals to company values\n\n"
          "❓ **What are your strengths?**\n"
          "• Choose 2-3 relevant strengths\n"
          "• Provide specific examples\n"
          "• Show how they apply to the role\n\n"
          "❓ **What are your weaknesses?**\n"
          "• Choose a real but minor weakness\n"
          "• Show how you're working to improve it\n"
          "• Turn it into a positive\n\n"
          "❓ **Where do you see yourself in 5 years?**\n"
          "• Show ambition but be realistic\n"
          "• Align with company growth opportunities\n"
          "• Demonstrate commitment to learning";
    }

    if (message.contains('resume') || message.contains('cv')) {
      return "Resume tips for placement interviews:\n\n"
          "📄 **Format:**\n"
          "• Keep it to 1-2 pages\n"
          "• Use clear, readable fonts\n"
          "• Organize sections logically\n"
          "• Use bullet points for readability\n\n"
          "📝 **Content:**\n"
          "• Include relevant projects with descriptions\n"
          "• Highlight technical skills\n"
          "• Quantify achievements (e.g., 'Improved performance by 30%')\n"
          "• Include internships, projects, and certifications\n"
          "• Add links to GitHub, LinkedIn, portfolio\n\n"
          "✅ **Tips:**\n"
          "• Tailor resume for each application\n"
          "• Use action verbs (Developed, Implemented, Optimized)\n"
          "• Proofread carefully\n"
          "• Keep it updated\n\n"
          "💡 You can upload your resume in the **Resume Gallery** section!";
    }

    if (message.contains('thank') || message.contains('thanks')) {
      return "You're welcome! 😊\n\n"
          "Remember:\n"
          "• Practice regularly\n"
          "• Stay confident\n"
          "• Learn from each interview\n"
          "• Keep improving your skills\n\n"
          "Good luck with your interviews! 🍀\n\n"
          "Feel free to ask me anything else about interview preparation!";
    }

    // Default response with helpful suggestions
    return "I understand you're asking about: \"$userMessage\"\n\n"
        "I can help you with:\n\n"
        "💼 **Interview Preparation:**\n"
        "• Ask: 'interview tips'\n"
        "• Ask: 'technical interview'\n"
        "• Ask: 'common questions'\n\n"
        "🎯 **Skills & Learning:**\n"
        "• Ask: 'what skills should I learn'\n"
        "• Ask: 'how to prepare'\n\n"
        "🏢 **Company Information:**\n"
        "• Ask: 'companies I applied to'\n"
        "• Ask: 'company requirements'\n\n"
        "📄 **Resume Help:**\n"
        "• Ask: 'resume tips'\n\n"
        "Try asking me one of these questions, or ask something specific about interview preparation!";
  }

  /// Send user message and get chatbot response
  Future<void> sendMessageAndGetResponse(String userMessage, String userId) async {
    try {
      // Save user message
      await _firestore.collection('chats').add({
        'senderId': userId,
        'receiverId': 'chatbot',
        'message': userMessage,
        'isRead': true,
        'timestamp': FieldValue.serverTimestamp(),
      });

      // Generate and save bot response
      final botResponse = await generateResponse(userMessage, userId);
      
      // Small delay to make it feel natural
      await Future.delayed(const Duration(milliseconds: 500));

      // Save bot response
      await _firestore.collection('chats').add({
        'senderId': 'chatbot',
        'receiverId': userId,
        'message': botResponse,
        'isRead': false,
        'timestamp': FieldValue.serverTimestamp(),
      });
    } catch (e) {
      print('Error in chatbot: $e');
      rethrow;
    }
  }
}

