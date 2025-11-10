import 'package:flutter/material.dart';
import '../services/firebase_service.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class SuggestionsScreen extends StatefulWidget {
  const SuggestionsScreen({super.key});

  @override
  State<SuggestionsScreen> createState() => _SuggestionsScreenState();
}

class _SuggestionsScreenState extends State<SuggestionsScreen> {
  final FirebaseService _firebaseService = FirebaseService();
  List<Map<String, dynamic>> _suggestions = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSuggestions();
  }

  Future<void> _loadSuggestions() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final user = _firebaseService.getCurrentUser();
      if (user == null) {
        setState(() {
          _error = 'Please login to see suggestions';
          _isLoading = false;
        });
        return;
      }

      // Get all applications for the user
      final applicationsSnapshot = await FirebaseFirestore.instance
          .collection('applications')
          .where('userId', isEqualTo: user.uid)
          .where('status', isEqualTo: 'applied')
          .get();

      if (applicationsSnapshot.docs.isEmpty) {
        setState(() {
          _suggestions = [
            {
              'type': 'info',
              'title': 'No Applications Yet',
              'description': 'Apply to companies to get personalized interview preparation suggestions!',
              'icon': Icons.info_outline,
              'color': Colors.blue,
            },
            {
              'type': 'general',
              'title': 'General Tips',
              'description': '• Practice Data Structures and Algorithms daily\n• Prepare your resume\n• Research companies before applying',
              'icon': Icons.lightbulb_outline,
              'color': Colors.orange,
            },
          ];
          _isLoading = false;
        });
        return;
      }

      final suggestions = <Map<String, dynamic>>[];
      final companyIds = <String>{};

      // Get company IDs from applications
      for (var app in applicationsSnapshot.docs) {
        final appData = app.data();
        final companyId = appData['companyId'] as String?;
        final companyName = appData['companyName'] as String? ?? 'Company';
        
        if (companyId != null) {
          companyIds.add(companyId);
        }

        // Add application-based suggestion
        suggestions.add({
          'type': 'application',
          'title': 'Applied to $companyName',
          'description': 'You have applied to $companyName. Check the company details for specific requirements.',
          'icon': Icons.business,
          'color': Colors.green,
          'companyId': companyId,
          'companyName': companyName,
        });
      }

      // Get scraped company data for each applied company
      for (var companyId in companyIds) {
        try {
          final scrapedData = await _firebaseService.getScrapedCompany(companyId);
          if (scrapedData != null) {
            final companyName = scrapedData['name'] as String? ?? 'Company';
            final skills = (scrapedData['skills'] as List<dynamic>?) ?? [];
            final roles = (scrapedData['roles'] as List<dynamic>?) ?? [];
            final eligibility = scrapedData['eligibility'] as String? ?? '';
            final process = scrapedData['process'] as String? ?? '';

            // Generate interview prep suggestions based on company data
            if (skills.isNotEmpty) {
              final skillsList = skills.take(5).join(', ');
              suggestions.add({
                'type': 'skill',
                'title': 'Prepare for $companyName Interview',
                'description': 'Focus on these skills: $skillsList\n\nReview and practice these technologies before your interview.',
                'icon': Icons.code,
                'color': Colors.purple,
                'companyName': companyName,
              });
            }

            if (roles.isNotEmpty) {
              final rolesList = roles.take(3).join(', ');
              suggestions.add({
                'type': 'role',
                'title': 'Role-Specific Preparation',
                'description': 'Positions available: $rolesList\n\nResearch these roles and prepare role-specific questions.',
                'icon': Icons.work_outline,
                'color': Colors.blue,
                'companyName': companyName,
              });
            }

            if (eligibility.isNotEmpty) {
              suggestions.add({
                'type': 'eligibility',
                'title': 'Check Eligibility Requirements',
                'description': 'Eligibility: $eligibility\n\nMake sure you meet all the requirements.',
                'icon': Icons.check_circle_outline,
                'color': Colors.teal,
                'companyName': companyName,
              });
            }

            if (process.isNotEmpty) {
              suggestions.add({
                'type': 'process',
                'title': 'Interview Process for $companyName',
                'description': 'Hiring Process:\n$process\n\nPrepare for each stage of the interview process.',
                'icon': Icons.timeline,
                'color': Colors.indigo,
                'companyName': companyName,
              });
            }
          }
        } catch (e) {
          // Skip if company data not found
          print('Error loading company data for $companyId: $e');
        }
      }

      // Get user profile to compare skills
      try {
        final profile = await _firebaseService.getUserProfile();
        final userSkills = (profile?['skills'] as List<dynamic>?) ?? [];

        // Get all company skills from applied companies
        final allRequiredSkills = <String>{};
        for (var companyId in companyIds) {
          final scrapedData = await _firebaseService.getScrapedCompany(companyId);
          if (scrapedData != null) {
            final skills = (scrapedData['skills'] as List<dynamic>?) ?? [];
            for (var skill in skills) {
              allRequiredSkills.add(skill.toString().toLowerCase());
            }
          }
        }

        final userSkillsLower = userSkills.map((s) => s.toString().toLowerCase()).toSet();
        final missingSkills = allRequiredSkills.difference(userSkillsLower);

        if (missingSkills.isNotEmpty) {
          final missingSkillsList = missingSkills.take(5).join(', ');
          suggestions.add({
            'type': 'skill_gap',
            'title': 'Skills to Learn',
            'description': 'Based on your applications, consider learning: $missingSkillsList\n\nThese skills are commonly required by companies you\'ve applied to.',
            'icon': Icons.school,
            'color': Colors.orange,
          });
        }
      } catch (e) {
        print('Error comparing skills: $e');
      }

      // Add general interview prep suggestions
      suggestions.addAll([
        {
          'type': 'general',
          'title': 'General Interview Tips',
          'description': '• Practice common interview questions\n• Prepare STAR method for behavioral questions\n• Research the company culture\n• Prepare questions to ask the interviewer',
          'icon': Icons.tips_and_updates,
          'color': Colors.amber,
        },
        {
          'type': 'general',
          'title': 'Technical Preparation',
          'description': '• Review Data Structures and Algorithms\n• Practice coding problems on LeetCode/HackerRank\n• Prepare for system design questions\n• Review your projects and be ready to explain them',
          'icon': Icons.computer,
          'color': Colors.cyan,
        },
      ]);

      setState(() {
        _suggestions = suggestions;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load suggestions: $e';
        _isLoading = false;
        // Fallback suggestions
        _suggestions = [
          {
            'type': 'general',
            'title': 'General Tips',
            'description': '• Improve DSA skills\n• Practice coding problems\n• Prepare for technical interviews',
            'icon': Icons.lightbulb_outline,
            'color': Colors.blue,
          },
        ];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Interview Preparation Suggestions"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadSuggestions,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        _error!,
                        style: const TextStyle(color: Colors.red),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadSuggestions,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _suggestions.isEmpty
                  ? const Center(
                      child: Text(
                        'No suggestions available',
                        style: TextStyle(fontSize: 16),
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadSuggestions,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _suggestions.length,
                        itemBuilder: (context, index) {
                          final suggestion = _suggestions[index];
                          final type = suggestion['type'] as String? ?? 'general';
                          final title = suggestion['title'] as String? ?? 'Suggestion';
                          final description = suggestion['description'] as String? ?? '';
                          final icon = suggestion['icon'] as IconData? ?? Icons.info;
                          final color = suggestion['color'] as Color? ?? Colors.blue;
                          final companyName = suggestion['companyName'] as String?;

                          return Card(
                            margin: const EdgeInsets.symmetric(vertical: 8),
                            elevation: 2,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: color.withOpacity(0.2),
                                child: Icon(icon, color: color),
                              ),
                              title: Text(
                                title,
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                              subtitle: Padding(
                                padding: const EdgeInsets.only(top: 8),
                                child: Text(
                                  description,
                                  style: const TextStyle(fontSize: 14),
                                ),
                              ),
                              isThreeLine: true,
                              trailing: companyName != null
                                  ? IconButton(
                                      icon: const Icon(Icons.arrow_forward_ios, size: 16),
                                      onPressed: () {
                                        // Navigate to company detail if needed
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          SnackBar(
                                            content: Text('View $companyName details'),
                                          ),
                                        );
                                      },
                                    )
                                  : null,
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
