import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:io';

class FirebaseService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseStorage _storage = FirebaseStorage.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  // ==================== COMPANY METHODS ====================
  
  /// Fetch all companies from companies collection (admin-inserted records)
  Stream<List<Map<String, dynamic>>> getCompaniesStream() {
    return _firestore
        .collection('companies')
        .snapshots()
        .map((snapshot) => snapshot.docs.map((doc) {
              final data = doc.data();
              data['id'] = doc.id;
              return data;
            }).toList());
  }

  /// Fetch all companies once (admin-inserted records)
  Future<List<Map<String, dynamic>>> getCompanies() async {
    try {
      final snapshot = await _firestore.collection('companies').get();
      return snapshot.docs.map((doc) {
        final data = doc.data();
        data['id'] = doc.id;
        return data;
      }).toList();
    } catch (e) {
      throw Exception('Failed to fetch companies: $e');
    }
  }

  /// Get a single company by ID (admin-inserted record)
  Future<Map<String, dynamic>?> getCompany(String companyId) async {
    try {
      final doc = await _firestore.collection('companies').doc(companyId).get();
      if (doc.exists) {
        final data = doc.data()!;
        data['id'] = doc.id;
        return data;
      }
      return null;
    } catch (e) {
      throw Exception('Failed to fetch company: $e');
    }
  }

  /// Get scraped company data by ID
  Future<Map<String, dynamic>?> getScrapedCompany(String companyId) async {
    try {
      final doc = await _firestore.collection('companies_scraped').doc(companyId).get();
      if (doc.exists) {
        final data = doc.data()!;
        data['id'] = doc.id;
        return data;
      }
      return null;
    } catch (e) {
      throw Exception('Failed to fetch scraped company: $e');
    }
  }

  /// Stream scraped company data
  Stream<Map<String, dynamic>?> getScrapedCompanyStream(String companyId) {
    return _firestore
        .collection('companies_scraped')
        .doc(companyId)
        .snapshots()
        .map((snapshot) {
          if (snapshot.exists) {
            final data = snapshot.data()!;
            data['id'] = snapshot.id;
            return data;
          }
          return null;
        });
  }

  // ==================== CALENDAR/EVENTS METHODS ====================
  
  /// Get all events for the current user
  Stream<List<Map<String, dynamic>>> getEventsStream() {
    final user = _auth.currentUser;
    if (user == null) return Stream.value([]);
    
    return _firestore
        .collection('events')
        .where('userId', isEqualTo: user.uid)
        .snapshots()
        .map((snapshot) {
          final events = <Map<String, dynamic>>[];
          for (var doc in snapshot.docs) {
            final data = doc.data();
            data['id'] = doc.id;
            // Convert timestamp if needed
            if (data['date'] != null) {
              if (data['date'] is Timestamp) {
                data['date'] = (data['date'] as Timestamp).toDate().toString().split(' ')[0];
              } else if (data['date'] is String) {
                // Keep as string
              }
            }
            events.add(data);
          }
          // Sort by date if available
          events.sort((a, b) {
            final aDate = a["date"]?.toString() ?? '';
            final bDate = b["date"]?.toString() ?? '';
            return aDate.compareTo(bDate);
          });
          return events;
        });
  }

  /// Create a new event
  Future<String> createEvent({
    required String title,
    required String date,
    String? time,
    String? description,
    String? companyName,
  }) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final docRef = await _firestore.collection('events').add({
        'userId': user.uid,
        'title': title,
        'date': date,
        'time': time ?? '',
        'description': description ?? '',
        'company_name': companyName ?? '',
        'created_at': FieldValue.serverTimestamp(),
      });
      return docRef.id;
    } catch (e) {
      throw Exception('Failed to create event: $e');
    }
  }

  /// Delete an event
  Future<void> deleteEvent(String eventId) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final doc = await _firestore.collection('events').doc(eventId).get();
      if (doc.exists && doc.data()?['userId'] == user.uid) {
        await _firestore.collection('events').doc(eventId).delete();
      } else {
        throw Exception('Event not found or unauthorized');
      }
    } catch (e) {
      throw Exception('Failed to delete event: $e');
    }
  }

  /// Get all reminders for the current user
  Stream<List<Map<String, dynamic>>> getRemindersStream() {
    final user = _auth.currentUser;
    if (user == null) return Stream.value([]);
    
    return _firestore
        .collection("reminders")
        .where("userId", isEqualTo: user.uid)
        .snapshots()
        .map((snapshot) {
          final reminders = <Map<String, dynamic>>[];
          for (var doc in snapshot.docs) {
            final data = doc.data();
            data["id"] = doc.id;
            // Convert timestamp if needed
            if (data["reminderTime"] != null && data["reminderTime"] is Timestamp) {
              data["reminderTime"] = (data["reminderTime"] as Timestamp).toDate();
            }
            reminders.add(data);
          }
          // Sort by reminderTime
          reminders.sort((a, b) {
            final aTime = a["reminderTime"];
            final bTime = b["reminderTime"];
            if (aTime == null || bTime == null) return 0;
            if (aTime is DateTime && bTime is DateTime) {
              return aTime.compareTo(bTime);
            }
            return 0;
          });
          return reminders;
        });
  }

  /// Create a reminder
  Future<String> createReminder({
    required String title,
    required DateTime reminderTime,
    String? description,
    bool isCompleted = false,
  }) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final docRef = await _firestore.collection('reminders').add({
        'userId': user.uid,
        'title': title,
        'description': description ?? '',
        'reminderTime': Timestamp.fromDate(reminderTime),
        'isCompleted': isCompleted,
      });
      return docRef.id;
    } catch (e) {
      throw Exception('Failed to create reminder: $e');
    }
  }

  /// Delete a reminder
  Future<void> deleteReminder(String reminderId) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final doc = await _firestore.collection('reminders').doc(reminderId).get();
      if (doc.exists && doc.data()?['userId'] == user.uid) {
        await _firestore.collection('reminders').doc(reminderId).delete();
      } else {
        throw Exception('Reminder not found or unauthorized');
      }
    } catch (e) {
      throw Exception('Failed to delete reminder: $e');
    }
  }

  /// Update a reminder
  Future<void> updateReminder(String reminderId, Map<String, dynamic> data) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final doc = await _firestore.collection('reminders').doc(reminderId).get();
      if (doc.exists && doc.data()?['userId'] == user.uid) {
        // Convert reminderTime if it's a DateTime
        if (data['reminderTime'] != null && data['reminderTime'] is DateTime) {
          data['reminderTime'] = Timestamp.fromDate(data['reminderTime'] as DateTime);
        }
        await _firestore.collection('reminders').doc(reminderId).update(data);
      } else {
        throw Exception('Reminder not found or unauthorized');
      }
    } catch (e) {
      throw Exception('Failed to update reminder: $e');
    }
  }

  // ==================== CHAT METHODS ====================
  
  /// Get chat messages stream (using 'chats' collection as per schema)
  /// Gets messages where user is sender or receiver, including chatbot messages
  Stream<List<Map<String, dynamic>>> getChatMessagesStream() {
    final user = _auth.currentUser;
    if (user == null) return Stream.value([]);
    
    // Get messages where user is sender or receiver (including chatbot)
    return _firestore
        .collection('chats')
        .orderBy('timestamp', descending: true)
        .limit(100)
        .snapshots()
        .map((snapshot) {
          final messages = <Map<String, dynamic>>[];
          for (var doc in snapshot.docs) {
            final data = doc.data();
            final senderId = data['senderId'];
            final receiverId = data['receiverId'];
            
            // Include message if:
            // 1. User is sender
            // 2. User is receiver
            // 3. Receiver is 'global' (public chat)
            // 4. Chatbot conversation (user <-> chatbot)
            if (senderId == user.uid || 
                receiverId == user.uid || 
                receiverId == 'global' ||
                senderId == 'chatbot' ||
                receiverId == 'chatbot') {
              data['id'] = doc.id;
              // Convert timestamp
              if (data['timestamp'] != null && data['timestamp'] is Timestamp) {
                data['timestamp'] = (data['timestamp'] as Timestamp).toDate();
              }
              messages.add(data);
            }
          }
          
          // Sort by timestamp (oldest first)
          messages.sort((a, b) {
            final aTime = a['timestamp'] as DateTime?;
            final bTime = b['timestamp'] as DateTime?;
            if (aTime == null || bTime == null) return 0;
            return aTime.compareTo(bTime);
          });
          
          return messages;
        });
  }

  /// Send a chat message (using 'chats' collection schema)
  Future<void> sendChatMessage(String message, {String? receiverId}) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      await _firestore.collection('chats').add({
        'senderId': user.uid,
        'receiverId': receiverId ?? 'global', // Use 'global' for public chat or 'chatbot' for AI
        'message': message,
        'isRead': false,
        'timestamp': FieldValue.serverTimestamp(),
      });
    } catch (e) {
      throw Exception('Failed to send message: $e');
    }
  }

  /// Get user name by ID
  Future<String> getUserName(String userId) async {
    try {
      final userDoc = await _firestore.collection('users').doc(userId).get();
      if (userDoc.exists) {
        final data = userDoc.data()!;
        return data['name'] ?? data['displayName'] ?? 'User';
      }
      return 'User';
    } catch (e) {
      return 'User';
    }
  }

  /// Mark message as read
  Future<void> markMessageRead(String messageId) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final messageRef = _firestore.collection('chats').doc(messageId);
      final messageDoc = await messageRef.get();
      
      if (messageDoc.exists) {
        final data = messageDoc.data()!;
        // Only mark as read if user is the receiver
        if (data['receiverId'] == user.uid) {
          await messageRef.update({'isRead': true});
        }
      }
    } catch (e) {
      throw Exception('Failed to mark message as read: $e');
    }
  }

  // ==================== RESUME/UPLOAD METHODS ====================
  
  /// Upload resume to Firebase Storage
  Future<String> uploadResume(File file, {Function(double)? onProgress}) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final fileName = 'resumes/${user.uid}/${DateTime.now().millisecondsSinceEpoch}_${file.path.split('/').last}';
      final ref = _storage.ref().child(fileName);
      
      final uploadTask = ref.putFile(
        file,
        SettableMetadata(
          contentType: 'application/pdf',
          customMetadata: {'uploadedBy': user.uid},
        ),
      );

      // Listen to upload progress
      uploadTask.snapshotEvents.listen((taskSnapshot) {
        final progress = taskSnapshot.bytesTransferred / taskSnapshot.totalBytes;
        onProgress?.call(progress);
      });

      await uploadTask;
      final downloadUrl = await ref.getDownloadURL();

      // Save resume metadata to Firestore
      await _firestore.collection('resumes').add({
        'userId': user.uid,
        'fileName': file.path.split('/').last,
        'downloadUrl': downloadUrl,
        'storagePath': fileName,
        'uploadedAt': FieldValue.serverTimestamp(),
      });

      return downloadUrl;
    } catch (e) {
      throw Exception('Failed to upload resume: $e');
    }
  }

  /// Get user's resumes
  Stream<List<Map<String, dynamic>>> getResumesStream() {
    final user = _auth.currentUser;
    if (user == null) return Stream.value([]);
    
    return _firestore
        .collection('resumes')
        .where('userId', isEqualTo: user.uid)
        .snapshots()
        .map((snapshot) {
          final resumes = <Map<String, dynamic>>[];
          for (var doc in snapshot.docs) {
            final data = doc.data();
            data['id'] = doc.id;
            if (data['uploadedAt'] != null) {
              data['uploadedAt'] = (data['uploadedAt'] as Timestamp).toDate();
            }
            resumes.add(data);
          }
          // Sort by uploadedAt in memory (newest first) to avoid index requirement
          resumes.sort((a, b) {
            final aDate = a['uploadedAt'];
            final bDate = b['uploadedAt'];
            if (aDate == null && bDate == null) return 0;
            if (aDate == null) return 1; // Null dates go to end
            if (bDate == null) return -1;
            if (aDate is DateTime && bDate is DateTime) {
              return bDate.compareTo(aDate); // Descending (newest first)
            }
            return 0;
          });
          return resumes;
        });
  }

  /// Delete a resume
  Future<void> deleteResume(String resumeId) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final doc = await _firestore.collection('resumes').doc(resumeId).get();
      if (doc.exists && doc.data()?['userId'] == user.uid) {
        // Delete from Storage
        final storagePath = doc.data()?['storagePath'];
        if (storagePath != null) {
          await _storage.ref().child(storagePath).delete();
        }
        // Delete from Firestore
        await _firestore.collection('resumes').doc(resumeId).delete();
      } else {
        throw Exception('Resume not found or unauthorized');
      }
    } catch (e) {
      throw Exception('Failed to delete resume: $e');
    }
  }

  // ==================== USER PROFILE METHODS ====================
  
  /// Get user profile
  Future<Map<String, dynamic>?> getUserProfile() async {
    final user = _auth.currentUser;
    if (user == null) return null;

    try {
      final doc = await _firestore.collection('users').doc(user.uid).get();
      if (doc.exists) {
        return doc.data();
      }
      return null;
    } catch (e) {
      throw Exception('Failed to fetch profile: $e');
    }
  }

  /// Update user profile
  Future<void> updateUserProfile(Map<String, dynamic> data) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      await _firestore.collection('users').doc(user.uid).set(data, SetOptions(merge: true));
    } catch (e) {
      throw Exception('Failed to update profile: $e');
    }
  }

  // ==================== APPLICATIONS METHODS ====================
  
  /// Apply for a company with optional deadline and interview date
  Future<void> applyForCompany(
    String companyId,
    String companyName, {
    String? deadline,
    String? interviewDate,
  }) async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      // Default deadline: 7 days from now if not provided
      final defaultDeadline = deadline ?? 
          DateTime.now().add(const Duration(days: 7)).toIso8601String().split('T')[0];
      
      final applicationData = {
        'userId': user.uid,
        'companyId': companyId,
        'companyName': companyName,
        'status': 'applied',
        'appliedAt': FieldValue.serverTimestamp(),
        'deadline': defaultDeadline, // Always add a deadline for countdown notifications
      };
      
      // Override with provided deadline if exists
      if (deadline != null && deadline.isNotEmpty) {
        applicationData['deadline'] = deadline;
      }
      
      // Add interview date if provided
      if (interviewDate != null && interviewDate.isNotEmpty) {
        applicationData['interviewDate'] = interviewDate;
        applicationData['interview_date'] = interviewDate; // For backend compatibility
      }
      
      final appDocRef = await _firestore.collection('applications').add(applicationData);
      final applicationId = appDocRef.id;

      // Auto-create calendar event
      await createEvent(
        title: 'Applied to $companyName',
        date: applicationData['deadline'] as String,
        time: '10:00 AM',
        description: 'Application submitted for $companyName',
        companyName: companyName,
      );
      
      // Create initial notification
      await _firestore.collection('notifications').add({
        'userId': user.uid,
        'title': 'Application Submitted',
        'message': 'Your application for $companyName has been submitted successfully!',
        'type': 'info',
        'companyName': companyName,
        'applicationId': applicationId,
        'isRead': false,
        'createdAt': FieldValue.serverTimestamp(),
      });
      
      // Create deadline countdown notification
      await _createDeadlineNotification(
        userId: user.uid,
        companyName: companyName,
        deadline: applicationData['deadline'] as String,
        applicationId: applicationId,
      );
      
      // Create interview notification if provided
      if (interviewDate != null && interviewDate.isNotEmpty) {
        await _createInterviewNotification(
          userId: user.uid,
          companyName: companyName,
          interviewDate: interviewDate,
          applicationId: applicationId,
        );
      }
    } catch (e) {
      throw Exception('Failed to apply: $e');
    }
  }
  
  /// Create deadline countdown notification
  Future<void> _createDeadlineNotification({
    required String userId,
    required String companyName,
    required String deadline,
    String? applicationId,
  }) async {
    try {
      final deadlineDate = DateTime.parse(deadline);
      final now = DateTime.now();
      final daysRemaining = deadlineDate.difference(now).inDays;
      
      String title;
      String message;
      String type;
      
      if (daysRemaining < 0) {
        title = 'Deadline Passed';
        message = 'The application deadline for $companyName has passed.';
        type = 'reminder';
      } else if (daysRemaining == 0) {
        title = 'Deadline Today!';
        message = '⏰ The application deadline for $companyName is TODAY! Submit your application now.';
        type = 'deadline';
      } else if (daysRemaining == 1) {
        title = 'Deadline Tomorrow!';
        message = '⏰ Only 1 day left! The application deadline for $companyName is tomorrow.';
        type = 'deadline';
      } else if (daysRemaining <= 3) {
        title = '$daysRemaining Days Left!';
        message = '⏰ Only $daysRemaining days left! The application deadline for $companyName is approaching.';
        type = 'deadline';
      } else if (daysRemaining <= 7) {
        title = '$daysRemaining Days Remaining';
        message = '📅 $daysRemaining days are left for $companyName application deadline. Prepare your documents!';
        type = 'reminder';
      } else {
        title = '$daysRemaining Days Remaining';
        message = '📅 $daysRemaining days are left for $companyName application deadline.';
        type = 'reminder';
      }
      
      await _firestore.collection('notifications').add({
        'userId': userId,
        'title': title,
        'message': message,
        'type': type,
        'companyName': companyName,
        'applicationId': applicationId,
        'isRead': false,
        'createdAt': FieldValue.serverTimestamp(),
      });
    } catch (e) {
      print('Error creating deadline notification: $e');
    }
  }
  
  /// Create interview reminder notification
  Future<void> _createInterviewNotification({
    required String userId,
    required String companyName,
    required String interviewDate,
    String? applicationId,
  }) async {
    try {
      final interviewDateTime = DateTime.parse(interviewDate);
      final now = DateTime.now();
      final daysUntil = interviewDateTime.difference(now).inDays;
      
      if (daysUntil < 0) return; // Don't create notification for past interviews
      
      String title;
      String message;
      
      if (daysUntil == 0) {
        title = 'Interview Today!';
        message = '🎯 Your interview with $companyName is TODAY! Good luck!';
      } else if (daysUntil == 1) {
        title = 'Interview Tomorrow!';
        message = '🎯 Your interview with $companyName is tomorrow. Prepare well!';
      } else if (daysUntil <= 3) {
        title = 'Interview in $daysUntil Days';
        message = '🎯 Your interview with $companyName is in $daysUntil days. Start preparing!';
      } else {
        title = 'Interview Scheduled';
        message = '📅 Your interview with $companyName is scheduled in $daysUntil days.';
      }
      
      await _firestore.collection('notifications').add({
        'userId': userId,
        'title': title,
        'message': message,
        'type': 'interview',
        'companyName': companyName,
        'applicationId': applicationId,
        'isRead': false,
        'createdAt': FieldValue.serverTimestamp(),
      });
    } catch (e) {
      print('Error creating interview notification: $e');
    }
  }
  
  /// Generate notifications for all existing applications (helper function)
  Future<void> generateNotificationsForExistingApplications() async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not authenticated');

    try {
      final applications = await _firestore
          .collection('applications')
          .where('userId', isEqualTo: user.uid)
          .where('status', isEqualTo: 'applied')
          .get();

      for (var appDoc in applications.docs) {
        final appData = appDoc.data();
        final companyName = appData['companyName'] ?? 'Company';
        final deadline = appData['deadline'];
        final interviewDate = appData['interviewDate'] ?? appData['interview_date'];
        final applicationId = appDoc.id;

        // Check if notification already exists
        final existingNotifications = await _firestore
            .collection('notifications')
            .where('userId', isEqualTo: user.uid)
            .where('applicationId', isEqualTo: applicationId)
            .get();

        if (existingNotifications.docs.isEmpty) {
          // Create application confirmation notification
          await _firestore.collection('notifications').add({
            'userId': user.uid,
            'title': 'Application Submitted',
            'message': 'Your application for $companyName has been submitted successfully!',
            'type': 'info',
            'companyName': companyName,
            'applicationId': applicationId,
            'isRead': false,
            'createdAt': FieldValue.serverTimestamp(),
          });
        }

        // Create deadline notification if deadline exists
        if (deadline != null) {
          final deadlineStr = deadline is String ? deadline : deadline.toString();
          await _createDeadlineNotification(
            userId: user.uid,
            companyName: companyName,
            deadline: deadlineStr,
            applicationId: applicationId,
          );
        }

        // Create interview notification if interview date exists
        if (interviewDate != null) {
          final interviewStr = interviewDate is String ? interviewDate : interviewDate.toString();
          await _createInterviewNotification(
            userId: user.uid,
            companyName: companyName,
            interviewDate: interviewStr,
            applicationId: applicationId,
          );
        }
      }
    } catch (e) {
      print('Error generating notifications: $e');
    }
  }

  // ==================== NOTIFICATIONS METHODS ====================
  
  /// Get notifications stream
  Stream<List<Map<String, dynamic>>> getNotificationsStream() {
    final user = _auth.currentUser;
    if (user == null) return Stream.value([]);

    return _firestore
        .collection('notifications')
        .where('userId', isEqualTo: user.uid)
        .orderBy('createdAt', descending: true)
        .limit(50)
        .snapshots()
        .map((snapshot) => snapshot.docs.map((doc) {
              final data = doc.data();
              data['id'] = doc.id;
              if (data['createdAt'] != null) {
                data['createdAt'] = (data['createdAt'] as Timestamp).toDate();
              }
              return data;
            }).toList());
  }

  // ==================== UTILITY METHODS ====================
  
  /// Get current user ID
  String? getCurrentUserId() {
    return _auth.currentUser?.uid;
  }

  /// Get current user
  User? getCurrentUser() {
    return _auth.currentUser;
  }
}

