
// import 'package:flutter/material.dart';
// import 'package:file_picker/file_picker.dart';

// class ProfileSetupScreen extends StatefulWidget {
//   const ProfileSetupScreen({super.key});

//   @override
//   State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
// }

// class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
//   final _formKey = GlobalKey<FormState>();

//   final _nameController = TextEditingController();
//   final _educationController = TextEditingController();
//   final _yearController = TextEditingController();
//   final _departmentController = TextEditingController();
//   final _technicalSkillsController = TextEditingController();
//   final _softSkillsController = TextEditingController();

//   String? _resumeFileName;

//   Future<void> _pickResume() async {
//     final result = await FilePicker.platform.pickFiles(
//       type: FileType.custom,
//       allowedExtensions: ['pdf'],
//     );
//     if (result != null) {
//       setState(() => _resumeFileName = result.files.single.name);
//       ScaffoldMessenger.of(context).showSnackBar(
//         SnackBar(content: Text("Selected Resume: ${result.files.single.name} ✅")),
//       );
//     }
//   }

//   void _saveProfile() {
//     if (_formKey.currentState!.validate()) {
//       ScaffoldMessenger.of(context).showSnackBar(
//         const SnackBar(content: Text("Profile saved successfully ✅")),
//       );

//       // For now, just navigate to home screen
//       Navigator.pushReplacementNamed(context, '/home');
//     }
//   }

//   Widget _buildTextField({
//     required TextEditingController controller,
//     required String label,
//     required IconData icon,
//     bool requiredField = true,
//   }) {
//     return TextFormField(
//       controller: controller,
//       validator: (value) {
//         if (requiredField && (value == null || value.isEmpty)) {
//           return "$label is required";
//         }
//         return null;
//       },
//       decoration: InputDecoration(
//         labelText: label,
//         prefixIcon: Icon(icon),
//         filled: true,
//         fillColor: Colors.white,
//         border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
//       ),
//     );
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       backgroundColor: const Color(0xFFEEF2F7),
//       appBar: AppBar(title: const Text("Complete Your Profile")),
//       body: SingleChildScrollView(
//         padding: const EdgeInsets.all(16),
//         child: Form(
//           key: _formKey,
//           child: Column(
//             children: [
//               _buildTextField(controller: _nameController, label: "Full Name", icon: Icons.person),
//               const SizedBox(height: 12),
//               _buildTextField(controller: _educationController, label: "Education", icon: Icons.school),
//               const SizedBox(height: 12),
//               _buildTextField(controller: _yearController, label: "Year of Study", icon: Icons.calendar_today),
//               const SizedBox(height: 12),
//               _buildTextField(controller: _departmentController, label: "Department", icon: Icons.apartment),
//               const SizedBox(height: 12),
//               _buildTextField(controller: _technicalSkillsController, label: "Technical Skills (comma separated)", icon: Icons.computer),
//               const SizedBox(height: 12),
//               _buildTextField(controller: _softSkillsController, label: "Soft Skills (comma separated)", icon: Icons.people_alt, requiredField: false),
//               const SizedBox(height: 20),

//               // Resume Upload
//               OutlinedButton.icon(
//                 onPressed: _pickResume,
//                 icon: const Icon(Icons.upload_file),
//                 label: Text(_resumeFileName ?? "Upload Resume (PDF)"),
//                 style: OutlinedButton.styleFrom(
//                   padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
//                   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
//                 ),
//               ),

//               const SizedBox(height: 24),

//               SizedBox(
//                 width: double.infinity,
//                 child: ElevatedButton(
//                   onPressed: _saveProfile,
//                   style: ElevatedButton.styleFrom(
//                     padding: const EdgeInsets.symmetric(vertical: 16),
//                     backgroundColor: Colors.blue,
//                     shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
//                   ),
//                   child: const Text("Save & Continue", style: TextStyle(fontSize: 16)),
//                 ),
//               ),
//             ],
//           ),
//         ),
//       ),
//     );
//   }
// }

import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class ProfileSetupScreen extends StatefulWidget {
  const ProfileSetupScreen({super.key});

  @override
  State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
  final _formKey = GlobalKey<FormState>();

  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _educationController = TextEditingController();
  final TextEditingController _yearController = TextEditingController();
  final TextEditingController _departmentController = TextEditingController();
  final TextEditingController _technicalSkillsController = TextEditingController();
  final TextEditingController _softSkillsController = TextEditingController();

  Uint8List? _resumeBytes;
  String? _resumeFileName;
  bool _isUploading = false;
  double _uploadProgress = 0.0;
  String? _resumeUrl;

  @override
  void dispose() {
    _nameController.dispose();
    _educationController.dispose();
    _yearController.dispose();
    _departmentController.dispose();
    _technicalSkillsController.dispose();
    _softSkillsController.dispose();
    super.dispose();
  }

  Future<void> _pickResume() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'doc', 'docx'],
        withData: true, // important: gives bytes that we can upload on web & mobile
      );

      if (result == null) {
        // user cancelled
        return;
      }

      final file = result.files.single;

      if (file.bytes == null) {
        // should be rare when withData:true, but handle gracefully
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Unable to read file bytes. Try again.")),
        );
        return;
      }

      setState(() {
        _resumeBytes = file.bytes;
        _resumeFileName = file.name;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Selected: ${file.name}")),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("File pick failed: $e")),
      );
    }
  }

  String _mimeFromExtension(String ext) {
    switch (ext.toLowerCase()) {
      case 'pdf':
        return 'application/pdf';
      case 'doc':
        return 'application/msword';
      case 'docx':
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      default:
        return 'application/octet-stream';
    }
  }

  Future<String?> _uploadResumeBytes(String uid) async {
    if (_resumeBytes == null || _resumeFileName == null) return null;

    setState(() {
      _isUploading = true;
      _uploadProgress = 0.0;
    });

    try {
      final ext = (_resumeFileName!.contains('.'))
          ? _resumeFileName!.split('.').last
          : 'pdf';
      final contentType = _mimeFromExtension(ext);

      final storagePath = 'resumes/$uid/${DateTime.now().millisecondsSinceEpoch}_$_resumeFileName';
      final ref = FirebaseStorage.instance.ref(storagePath);

      final metadata = SettableMetadata(contentType: contentType);

      final uploadTask = ref.putData(_resumeBytes!, metadata);

      uploadTask.snapshotEvents.listen((TaskSnapshot snap) {
        final bytesTransferred = snap.bytesTransferred;
        final totalBytes = snap.totalBytes;
        if (totalBytes > 0) {
          setState(() => _uploadProgress = bytesTransferred / totalBytes);
        }
      });

      final snapshot = await uploadTask;
      final downloadUrl = await snapshot.ref.getDownloadURL();

      setState(() {
        _resumeUrl = downloadUrl;
      });

      return downloadUrl;
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Upload failed: $e")),
      );
      return null;
    } finally {
      setState(() {
        _isUploading = false;
        _uploadProgress = 0.0;
      });
    }
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;

    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Not signed in.")),
      );
      return;
    }

    try {
      // If user picked a resume and not uploaded yet -> upload
      if (_resumeBytes != null && (_resumeUrl == null || _resumeUrl!.isEmpty)) {
        await _uploadResumeBytes(user.uid);
      }

      final data = {
        'name': _nameController.text.trim(),
        'education': _educationController.text.trim(),
        'year': _yearController.text.trim(),
        'department': _departmentController.text.trim(),
        'technicalSkills': _technicalSkillsController.text
            .split(',')
            .map((s) => s.trim())
            .where((s) => s.isNotEmpty)
            .toList(),
        'softSkills': _softSkillsController.text
            .split(',')
            .map((s) => s.trim())
            .where((s) => s.isNotEmpty)
            .toList(),
        'isProfileComplete': true,
        'resumeUrl': _resumeUrl ?? '',
        'updatedAt': FieldValue.serverTimestamp(),
      };

      await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .set(data, SetOptions(merge: true));

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Profile saved successfully ✅")),
      );

      Navigator.pushReplacementNamed(context, '/home');
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to save profile: $e")),
      );
    }
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool requiredField = true,
  }) {
    return TextFormField(
      controller: controller,
      validator: (value) {
        if (requiredField && (value == null || value.isEmpty)) {
          return "$label is required";
        }
        return null;
      },
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final fileLabel = _resumeFileName ?? "Upload Resume (PDF/DOC/DOCX)";

    return Scaffold(
      backgroundColor: const Color(0xFFEEF2F7),
      appBar: AppBar(title: const Text("Complete Your Profile")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              _buildTextField(controller: _nameController, label: "Full Name", icon: Icons.person),
              const SizedBox(height: 12),
              _buildTextField(controller: _educationController, label: "Education", icon: Icons.school),
              const SizedBox(height: 12),
              _buildTextField(controller: _yearController, label: "Year of Study", icon: Icons.calendar_today),
              const SizedBox(height: 12),
              _buildTextField(controller: _departmentController, label: "Department", icon: Icons.apartment),
              const SizedBox(height: 12),
              _buildTextField(controller: _technicalSkillsController, label: "Technical Skills (comma separated)", icon: Icons.computer),
              const SizedBox(height: 12),
              _buildTextField(controller: _softSkillsController, label: "Soft Skills (comma separated)", icon: Icons.people_alt, requiredField: false),
              const SizedBox(height: 20),

              Row(
                children: [
                  OutlinedButton.icon(
                    onPressed: _isUploading ? null : _pickResume,
                    icon: const Icon(Icons.upload_file),
                    label: Text(fileLabel),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  if (_resumeUrl != null && _resumeUrl!.isNotEmpty)
                    IconButton(
                      tooltip: "Open uploaded resume",
                      icon: const Icon(Icons.open_in_new),
                      onPressed: () {
                        // open in browser - works on web and mobile if a browser is available
                        // You can use url_launcher package to open link. Keeping lightweight here.
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text("Resume uploaded — open it from profile or gallery.")),
                        );
                      },
                    ),
                ],
              ),

              if (_isUploading)
                Padding(
                  padding: const EdgeInsets.only(top: 12.0),
                  child: Column(
                    children: [
                      LinearProgressIndicator(value: _uploadProgress),
                      const SizedBox(height: 8),
                      Text("${(_uploadProgress * 100).toStringAsFixed(0)}% uploaded"),
                    ],
                  ),
                ),

              const SizedBox(height: 24),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isUploading ? null : _saveProfile,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    backgroundColor: Colors.blue,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isUploading ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Text("Save & Continue", style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
