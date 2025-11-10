import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../services/firebase_service.dart';
import '../services/backend_api_service.dart';
import 'company_detail_screen.dart';

class CompanyListScreen extends StatefulWidget {
  const CompanyListScreen({super.key});

  @override
  State<CompanyListScreen> createState() => _CompanyListScreenState();
}

class _CompanyListScreenState extends State<CompanyListScreen> {
  final FirebaseService _firebaseService = FirebaseService();
  List<Map<String, dynamic>> _companies = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadCompanies();
  }

  Future<void> _loadCompanies() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Load companies from Firestore (admin-inserted records)
      final companies = await _firebaseService.getCompanies();
      setState(() {
        _companies = companies;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load companies: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Companies"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadCompanies,
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
                        onPressed: _loadCompanies,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _companies.isEmpty
                  ? const Center(
                      child: Text(
                        'No companies found',
                        style: TextStyle(fontSize: 16),
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadCompanies,
                      child: StreamBuilder<List<Map<String, dynamic>>>(
                        stream: _firebaseService.getCompaniesStream(),
                        builder: (context, snapshot) {
                          final companies = snapshot.hasData 
                              ? snapshot.data! 
                              : _companies;

                          return ListView.builder(
                            itemCount: companies.length,
                            itemBuilder: (context, index) {
                              final company = companies[index];
                              final companyName = company['company_name'] ?? company['name'] ?? 'Unknown Company';
                              final visitDate = company['visit_date'];
                              final visitTime = company['visit_time'];

                              return Card(
                                margin: const EdgeInsets.symmetric(
                                  horizontal: 16,
                                  vertical: 8,
                                ),
                                child: ListTile(
                                  leading: CircleAvatar(
                                    child: Text(
                                      companyName[0].toUpperCase(),
                                      style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                  title: Text(
                                    companyName,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  subtitle: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      if (visitDate != null)
                                        Text('📅 Visit Date: ${_formatDate(visitDate)}'),
                                      if (visitTime != null)
                                        Text('🕐 Time: $visitTime'),
                                    ],
                                  ),
                                  trailing: const Icon(Icons.arrow_forward_ios),
                                  onTap: () {
                                    // Navigate to detail screen - scraping will happen automatically
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (_) => CompanyDetailScreen(
                                          companyId: company['id'],
                                          companyData: company,
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              );
                            },
                          );
                        },
                      ),
                    ),
    );
  }

  String _formatDate(dynamic date) {
    if (date == null) return '';
    try {
      if (date is Timestamp) {
        final dt = date.toDate();
        return '${dt.day}/${dt.month}/${dt.year}';
      } else if (date is String) {
        return date;
      }
      return date.toString();
    } catch (e) {
      return date.toString();
    }
  }
}
