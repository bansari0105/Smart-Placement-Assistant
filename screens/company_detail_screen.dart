import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../services/firebase_service.dart';
import '../services/backend_api_service.dart';

class CompanyDetailScreen extends StatefulWidget {
  final String companyId;
  final Map<String, dynamic>? companyData;

  const CompanyDetailScreen({
    super.key,
    required this.companyId,
    this.companyData,
  });

  @override
  State<CompanyDetailScreen> createState() => _CompanyDetailScreenState();
}

class _CompanyDetailScreenState extends State<CompanyDetailScreen> {
  final FirebaseService _firebaseService = FirebaseService();
  Map<String, dynamic>? _companyData; // Admin-inserted record
  Map<String, dynamic>? _scrapedData; // Scraped data
  bool _isLoadingScraped = false;
  bool _isScraping = false;
  String? _error;
  String? _scrapingError;

  @override
  void initState() {
    super.initState();
    _companyData = widget.companyData;
    if (_companyData == null) {
      _loadCompany();
    } else {
      _checkAndScrape();
    }
  }

  Future<void> _loadCompany() async {
    setState(() {
      _error = null;
    });

    try {
      final company = await _firebaseService.getCompany(widget.companyId);
      setState(() {
        _companyData = company;
      });
      if (company != null) {
        _checkAndScrape();
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to load company: $e';
      });
    }
  }

  Future<void> _checkAndScrape() async {
    if (_companyData == null) return;

    // Check if scraped data already exists
    setState(() {
      _isLoadingScraped = true;
    });

    try {
      // Try to get existing scraped data
      final existingScraped = await _firebaseService.getScrapedCompany(widget.companyId);
      
      if (existingScraped != null && existingScraped.isNotEmpty) {
        // Scraped data exists, use it
        setState(() {
          _scrapedData = existingScraped;
          _isLoadingScraped = false;
        });
      } else {
        // No scraped data, trigger scraping
        await _triggerScraping();
      }
    } catch (e) {
      // If error loading, try scraping
      await _triggerScraping();
    }

    // Also listen for real-time updates
    _firebaseService.getScrapedCompanyStream(widget.companyId).listen((scraped) {
      if (scraped != null && mounted) {
        setState(() {
          _scrapedData = scraped;
          _isLoadingScraped = false;
          _isScraping = false;
        });
      }
    });
  }

  Future<void> _triggerScraping() async {
    if (_isScraping) return; // Prevent multiple simultaneous scrapes

    setState(() {
      _isScraping = true;
      _scrapingError = null;
      _isLoadingScraped = true;
    });

    try {
      // Call backend to scrape company
      final result = await BackendApiService.scrapeCompanyById(widget.companyId);
      
      if (result != null && result['company'] != null) {
        setState(() {
          _scrapedData = result['company'] as Map<String, dynamic>;
          _isScraping = false;
          _isLoadingScraped = false;
        });
      } else {
        setState(() {
          _scrapingError = 'Failed to scrape company data';
          _isScraping = false;
          _isLoadingScraped = false;
        });
      }
    } catch (e) {
      setState(() {
        _scrapingError = 'Error scraping company: $e';
        _isScraping = false;
        _isLoadingScraped = false;
      });
    }
  }

  Future<void> _applyForCompany() async {
    if (_companyData == null) return;

    try {
      final companyName = _companyData!['company_name'] ?? _companyData!['name'] ?? 'Unknown Company';
      await _firebaseService.applyForCompany(
        widget.companyId,
        companyName,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Applied to $companyName!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to apply: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_companyData == null && _error == null) {
      return Scaffold(
        appBar: AppBar(title: const Text("Company Details")),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null && _companyData == null) {
      return Scaffold(
        appBar: AppBar(title: const Text("Company Details")),
        body: Center(
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
                onPressed: _loadCompany,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    final company = _companyData!;
    final companyName = company['company_name'] ?? company['name'] ?? 'Unknown Company';
    final visitDate = company['visit_date'];
    final visitTime = company['visit_time'];

    return Scaffold(
      appBar: AppBar(
        title: Text(companyName),
        actions: [
          if (_isScraping)
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          else
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: _triggerScraping,
              tooltip: 'Refresh scraped data',
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Company Name
            Text(
              companyName,
              style: const TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),

            // Visit Information
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Visit Information",
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (visitDate != null)
                      Row(
                        children: [
                          const Icon(Icons.calendar_today, color: Colors.blue),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Visit Date: ${_formatDate(visitDate)}',
                              style: const TextStyle(fontSize: 16),
                            ),
                          ),
                        ],
                      ),
                    if (visitTime != null) ...[
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(Icons.access_time, color: Colors.blue),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Time: $visitTime',
                              style: const TextStyle(fontSize: 16),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Scraped Data Section
            if (_isScraping || _isLoadingScraped)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(
                    child: Column(
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Scraping company information...'),
                        SizedBox(height: 8),
                        Text(
                          'This may take a few moments',
                          style: TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else if (_scrapingError != null)
              Card(
                color: Colors.red.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Icon(Icons.error, color: Colors.red),
                      const SizedBox(height: 8),
                      Text(
                        _scrapingError!,
                        style: const TextStyle(color: Colors.red),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      ElevatedButton(
                        onPressed: _triggerScraping,
                        child: const Text('Retry Scraping'),
                      ),
                    ],
                  ),
                ),
              )
            else if (_scrapedData != null) ...[
              // Description
              if (_scrapedData!['description'] != null &&
                  _scrapedData!['description'].toString().isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "About",
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _scrapedData!['description'],
                          style: const TextStyle(fontSize: 16, height: 1.5),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Roles
              if (_scrapedData!['roles'] != null &&
                  (_scrapedData!['roles'] as List).isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Available Roles",
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: (_scrapedData!['roles'] as List)
                              .map<Widget>((role) {
                            return Chip(
                              label: Text(role.toString()),
                              backgroundColor: Colors.blue.shade50,
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Skills
              if (_scrapedData!['skills'] != null &&
                  (_scrapedData!['skills'] as List).isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Required Skills",
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: (_scrapedData!['skills'] as List)
                              .map<Widget>((skill) {
                            return Chip(
                              label: Text(skill.toString()),
                              backgroundColor: Colors.green.shade50,
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Eligibility
              if (_scrapedData!['eligibility'] != null &&
                  _scrapedData!['eligibility'].toString().isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Eligibility",
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _scrapedData!['eligibility'],
                          style: const TextStyle(fontSize: 16, height: 1.5),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Hiring Process
              if (_scrapedData!['process'] != null &&
                  _scrapedData!['process'].toString().isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Hiring Process",
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _scrapedData!['process'],
                          style: const TextStyle(fontSize: 16, height: 1.5),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Source URL
              if (_scrapedData!['source_url'] != null &&
                  _scrapedData!['source_url'].toString().isNotEmpty)
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.link, color: Colors.blue),
                    title: const Text("Source"),
                    subtitle: Text(_scrapedData!['source_url']),
                    onTap: () {
                      // Could open URL in browser
                    },
                  ),
                ),
            ]
            else
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Icon(Icons.info_outline, size: 48, color: Colors.grey),
                      const SizedBox(height: 8),
                      const Text(
                        'No scraped data available',
                        style: TextStyle(fontSize: 16),
                      ),
                      const SizedBox(height: 8),
                      ElevatedButton(
                        onPressed: _triggerScraping,
                        child: const Text('Scrape Company Data'),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 24),

            // Apply Button
            Center(
              child: ElevatedButton.icon(
                onPressed: _applyForCompany,
                icon: const Icon(Icons.send),
                label: const Text('Apply Now'),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(dynamic date) {
    if (date == null) return '';
    try {
      if (date is Timestamp) {
        return date.toDate().toString().split(' ')[0];
      } else if (date is String) {
        return date;
      }
      return date.toString();
    } catch (e) {
      return date.toString();
    }
  }
}
