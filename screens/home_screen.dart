// import 'package:flutter/material.dart';
// import 'profile_setup_screen.dart';
// import 'company_list_screen.dart';
// import 'notifications_screen.dart';
// import 'chat_screen.dart';
// import 'calender_screen.dart';
// import 'resume_gallery_screen.dart';
// import 'suggestions_screen.dart';

// class HomeScreen extends StatelessWidget {
//   const HomeScreen({super.key});

//   @override
//   Widget build(BuildContext context) {
//     final dummyProfile = {
//       "name": "John Doe",
//       "education": "B.Tech CSE",
//       "year": "3rd Year",
//       "department": "Computer Science",
//     };

//     return Scaffold(
//       backgroundColor: const Color(0xFFF5F6FA),
//       appBar: AppBar(
//         title: const Text("Smart Placement Assistant"),
//         backgroundColor: Colors.white,
//         elevation: 1,
//         leading: Builder(
//           builder: (context) => IconButton(
//             icon: const Icon(Icons.menu),
//             onPressed: () => Scaffold.of(context).openDrawer(),
//           ),
//         ),
//       ),

//       // ✅ Drawer Added
//       drawer: Drawer(
//         shape: const RoundedRectangleBorder(
//           borderRadius: BorderRadius.only(
//             topRight: Radius.circular(20),
//             bottomRight: Radius.circular(20),
//           ),
//         ),
//         child: Column(
//           crossAxisAlignment: CrossAxisAlignment.stretch,
//           children: [
//             UserAccountsDrawerHeader(
//               decoration: BoxDecoration(color: Colors.blue.shade600),
//               accountName: Text(dummyProfile["name"]!, style: const TextStyle(fontWeight: FontWeight.bold)),
//               accountEmail: Text("${dummyProfile["education"]!} | ${dummyProfile["year"]!}"),
//               currentAccountPicture: const CircleAvatar(
//                 backgroundColor: Colors.white,
//                 child: Icon(Icons.person, size: 40, color: Colors.blue),
//               ),
//             ),
//             ListTile(
//               leading: const Icon(Icons.person),
//               title: const Text("View / Edit Profile"),
//               onTap: () {
//                 Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileSetupScreen()));
//               },
//             ),
//             ListTile(
//               leading: const Icon(Icons.settings),
//               title: const Text("Settings"),
//               onTap: () {},
//             ),
//             const Spacer(),
//             const Divider(),
//             ListTile(
//               leading: const Icon(Icons.logout, color: Colors.red),
//               title: const Text("Logout", style: TextStyle(color: Colors.red)),
//               onTap: () {
//                 Navigator.pushReplacementNamed(context, '/login');
//               },
//             ),
//           ],
//         ),
//       ),

//       // ✅ Body is now just the dashboard grid (no profile card)
//       body: SafeArea(
//         child: GridView.count(
//           padding: const EdgeInsets.all(16),
//           crossAxisCount: 2,
//           crossAxisSpacing: 16,
//           mainAxisSpacing: 16,
//           children: [
//             _homeFeatureCard(context, "Suggestions", Icons.lightbulb, Colors.amber, const SuggestionsScreen()),
//             _homeFeatureCard(context, "Companies", Icons.business, Colors.blue, const CompanyListScreen()),
//             _homeFeatureCard(context, "Notifications", Icons.notifications, Colors.redAccent, const NotificationsScreen()),
//             _homeFeatureCard(context, "Calendar", Icons.calendar_today, Colors.green, const CalenderScreen()),
//             _homeFeatureCard(context, "Chat & Peer", Icons.chat_bubble_outline, Colors.deepPurple, const ChatScreen()),
//             _homeFeatureCard(context, "Resume Gallery", Icons.folder, Colors.orange, const ResumeGalleryScreen()),
//           ],
//         ),
//       ),
//     );
//   }

//   Widget _homeFeatureCard(BuildContext context, String title, IconData icon, Color color, Widget page) {
//     return GestureDetector(
//       onTap: () {
//         Navigator.push(context, MaterialPageRoute(builder: (_) => page));
//       },
//       child: Container(
//         decoration: BoxDecoration(
//           color: Colors.white,
//           borderRadius: BorderRadius.circular(16),
//           boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 6, offset: const Offset(0, 3))],
//         ),
//         child: Column(
//           mainAxisAlignment: MainAxisAlignment.center,
//           children: [
//             CircleAvatar(
//               radius: 28,
//               backgroundColor: color.withOpacity(0.15),
//               child: Icon(icon, size: 28, color: color),
//             ),
//             const SizedBox(height: 10),
//             Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
//           ],
//         ),
//       ),
//     );
//   }
// }

import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../services/firebase_service.dart';
import 'profile_setup_screen.dart';
import 'company_list_screen.dart';
import 'notifications_screen.dart';
import 'chat_screen.dart';
import 'calender_screen.dart';
import 'resume_gallery_screen.dart';
import 'suggestions_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final FirebaseService _firebaseService = FirebaseService();
  Map<String, dynamic>? _userProfile;
  bool _isLoadingProfile = true;

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    try {
      final profile = await _firebaseService.getUserProfile();
      final user = _firebaseService.getCurrentUser();
      setState(() {
        _userProfile = profile;
        _isLoadingProfile = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingProfile = false;
      });
    }
  }

  Future<void> _logout() async {
    try {
      await FirebaseAuth.instance.signOut();
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/login');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Logout failed: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final userName = _userProfile?['name'] ?? 
                     _firebaseService.getCurrentUser()?.displayName ?? 
                     'User';
    final greeting = _getGreeting();
    
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FC),
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.transparent,
        leading: Builder(
          builder: (context) => IconButton(
            icon: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 10,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: const Icon(Icons.menu, color: Color(0xFF2D3748)),
            ),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: const Icon(Icons.notifications_none, color: Color(0xFF2D3748)),
          ),
        ],
      ),

      // ✅ Enhanced Drawer
      drawer: Drawer(
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.only(
            topRight: Radius.circular(30),
            bottomRight: Radius.circular(30),
          ),
        ),
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Colors.blue.shade600,
                Colors.blue.shade800,
              ],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
              Container(
                padding: const EdgeInsets.only(top: 60, left: 20, right: 20, bottom: 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 40,
                      backgroundColor: Colors.white,
                      child: Icon(Icons.person, size: 50, color: Colors.blue.shade700),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      userName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                _userProfile?['department'] != null 
                  ? "${_userProfile!['department']} | ${_userProfile?['graduation_year'] ?? ''}"
                  : _firebaseService.getCurrentUser()?.email ?? '',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.9),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Container(
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: Column(
                    children: [
                      const SizedBox(height: 20),
                      _drawerItem(Icons.person_outline, "View / Edit Profile", () {
                        Navigator.pop(context);
                Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileSetupScreen()));
                      }),
                      _drawerItem(Icons.settings_outlined, "Settings", () {
                        Navigator.pop(context);
                      }),
                      _drawerItem(Icons.help_outline, "Help & Support", () {
                        Navigator.pop(context);
                      }),
            const Spacer(),
            const Divider(),
                      _drawerItem(Icons.logout, "Logout", _logout, isLogout: true),
                      const SizedBox(height: 20),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),

      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Beautiful Header Section with Animation
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.0, end: 1.0),
                duration: const Duration(milliseconds: 800),
                curve: Curves.easeOut,
                builder: (context, value, child) {
                  return Transform.translate(
                    offset: Offset(0, 20 * (1 - value)),
                    child: Opacity(opacity: value, child: child),
                  );
                },
                child: Container(
                  margin: const EdgeInsets.all(20),
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        Colors.blue.shade600,
                        Colors.blue.shade700,
                        Colors.indigo.shade700,
                        Colors.purple.shade700,
                      ],
                      stops: const [0.0, 0.3, 0.7, 1.0],
                    ),
                    borderRadius: BorderRadius.circular(28),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.blue.withOpacity(0.4),
                        blurRadius: 25,
                        offset: const Offset(0, 12),
                        spreadRadius: -5,
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
        child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  greeting,
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.9),
                                    fontSize: 16,
                                    fontWeight: FontWeight.w500,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  userName.split(' ').first,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 32,
                                    fontWeight: FontWeight.bold,
                                    letterSpacing: -0.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: const Icon(
                              Icons.emoji_events,
                              color: Colors.white,
                              size: 28,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 20),
                      _AnimatedMotivationCard(),
                    ],
                  ),
                ),
              ),

              // Quick Stats Section with Animation
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.0, end: 1.0),
                duration: const Duration(milliseconds: 600),
                curve: Curves.easeOut,
                builder: (context, value, child) {
                  return Transform.translate(
                    offset: Offset(0, 15 * (1 - value)),
                    child: Opacity(opacity: value, child: child),
                  );
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Row(
          children: [
                      Expanded(
                        child: _statCard(
                          'Applications',
                          '0',
                          Icons.business_center,
                          [Colors.blue.shade400, Colors.blue.shade700],
                        ),
                      ),
                      const SizedBox(width: 12),
            Expanded(
                        child: _statCard(
                          'Interviews',
                          '0',
                          Icons.event,
                          [Colors.orange.shade400, Colors.deepOrange.shade600],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Features Grid with Staggered Animation
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Quick Access',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1A202C),
                        letterSpacing: -0.5,
                      ),
                    ),
                    const SizedBox(height: 20),
                    GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                      crossAxisSpacing: 18,
                      mainAxisSpacing: 18,
                      childAspectRatio: 0.88,
                children: [
                        _AnimatedGridItem(
                          delay: 0,
                          child: _homeFeatureCard(
                            context,
                            "Suggestions",
                            Icons.lightbulb_outline,
                            [Colors.amber.shade400, Colors.orange.shade600],
                            const SuggestionsScreen(),
                          ),
                        ),
                        _AnimatedGridItem(
                          delay: 100,
                          child: _homeFeatureCard(
                            context,
                            "Companies",
                            Icons.business_outlined,
                            [Colors.blue.shade400, Colors.blue.shade700],
                            const CompanyListScreen(),
                          ),
                        ),
                        _AnimatedGridItem(
                          delay: 200,
                          child: _homeFeatureCard(
                            context,
                            "Notifications",
                            Icons.notifications_outlined,
                            [Colors.red.shade400, Colors.pink.shade600],
                            const NotificationsScreen(),
                          ),
                        ),
                        _AnimatedGridItem(
                          delay: 300,
                          child: _homeFeatureCard(
                            context,
                            "Calendar",
                            Icons.calendar_today_outlined,
                            [Colors.green.shade400, Colors.teal.shade600],
                            const CalenderScreen(),
                          ),
                        ),
                        _AnimatedGridItem(
                          delay: 400,
                          child: _homeFeatureCard(
                            context,
                            "Chat & Peer",
                            Icons.chat_bubble_outline,
                            [Colors.purple.shade400, Colors.deepPurple.shade600],
                            const ChatScreen(),
                          ),
                        ),
                        _AnimatedGridItem(
                          delay: 500,
                          child: _homeFeatureCard(
                            context,
                            "Resume Gallery",
                            Icons.folder_outlined,
                            [Colors.orange.shade400, Colors.deepOrange.shade600],
                            const ResumeGalleryScreen(),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) {
      return 'Good Morning';
    } else if (hour < 17) {
      return 'Good Afternoon';
    } else {
      return 'Good Evening';
    }
  }

  Widget _statCard(String label, String value, IconData icon, List<Color> gradientColors) {
    return _AnimatedStatCard(
      label: label,
      value: value,
      icon: icon,
      gradientColors: gradientColors,
    );
  }

  Widget _drawerItem(IconData icon, String title, VoidCallback onTap, {bool isLogout = false}) {
    return ListTile(
      leading: Icon(
        icon,
        color: isLogout ? Colors.red : const Color(0xFF2D3748),
      ),
      title: Text(
        title,
        style: TextStyle(
          color: isLogout ? Colors.red : const Color(0xFF2D3748),
          fontWeight: FontWeight.w500,
        ),
      ),
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
    );
  }

  Widget _homeFeatureCard(
    BuildContext context,
    String title,
    IconData icon,
    List<Color> gradientColors,
    Widget page,
  ) {
    return _AnimatedFeatureCard(
      title: title,
      icon: icon,
      gradientColors: gradientColors,
      onTap: () {
        Navigator.push(
          context,
          PageRouteBuilder(
            pageBuilder: (context, animation, secondaryAnimation) => page,
            transitionsBuilder: (context, animation, secondaryAnimation, child) {
              return FadeTransition(opacity: animation, child: child);
            },
          ),
        );
      },
    );
  }
}

// Animated Stat Card with Scale Animation
class _AnimatedStatCard extends StatefulWidget {
  final String label;
  final String value;
  final IconData icon;
  final List<Color> gradientColors;

  const _AnimatedStatCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.gradientColors,
  });

  @override
  State<_AnimatedStatCard> createState() => _AnimatedStatCardState();
}

class _AnimatedStatCardState extends State<_AnimatedStatCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  bool _isPressed = false;
  bool _isHovered = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 180),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.05).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    setState(() => _isPressed = true);
    _controller.forward();
  }

  void _handleTapUp(TapUpDetails details) {
    setState(() => _isPressed = false);
    _controller.reverse();
  }

  void _handleTapCancel() {
    setState(() => _isPressed = false);
    _controller.reverse();
  }

  void _handleHoverEnter() {
    setState(() => _isHovered = true);
    _controller.forward();
  }

  void _handleHoverExit() {
    setState(() => _isHovered = false);
    if (!_isPressed) {
      _controller.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isActive = _isPressed || _isHovered;
    
    return MouseRegion(
      onEnter: (_) => _handleHoverEnter(),
      onExit: (_) => _handleHoverExit(),
      child: GestureDetector(
        onTapDown: _handleTapDown,
        onTapUp: _handleTapUp,
        onTapCancel: _handleTapCancel,
        child: ScaleTransition(
          scale: _scaleAnimation,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOut,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Colors.white,
                  widget.gradientColors[0].withOpacity(0.05),
                ],
              ),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: widget.gradientColors[0].withOpacity(isActive ? 0.2 : 0.1),
                width: isActive ? 1.5 : 1,
              ),
              boxShadow: [
                BoxShadow(
                  color: widget.gradientColors[0].withOpacity(isActive ? 0.2 : 0.1),
                  blurRadius: isActive ? 20 : 15,
                  offset: Offset(0, isActive ? 8 : 6),
                  spreadRadius: isActive ? 2 : 0,
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  curve: Curves.easeOut,
                  padding: EdgeInsets.all(isActive ? 12 : 10),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        widget.gradientColors[0].withOpacity(isActive ? 0.2 : 0.15),
                        widget.gradientColors[1].withOpacity(isActive ? 0.2 : 0.15),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    widget.icon,
                    color: widget.gradientColors[0],
                    size: isActive ? 24 : 22,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  widget.value,
                  style: TextStyle(
                    fontSize: isActive ? 30 : 28,
                    fontWeight: FontWeight.bold,
                    foreground: Paint()
                      ..shader = LinearGradient(
                        colors: widget.gradientColors,
                      ).createShader(const Rect.fromLTWH(0, 0, 200, 70)),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  widget.label,
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.grey.shade700,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.3,
              ),
            ),
          ],
            ),
          ),
        ),
      ),
    );
  }
}

// Animated Motivation Card in Header
class _AnimatedMotivationCard extends StatefulWidget {
  const _AnimatedMotivationCard();

  @override
  State<_AnimatedMotivationCard> createState() => _AnimatedMotivationCardState();
}

class _AnimatedMotivationCardState extends State<_AnimatedMotivationCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  bool _isPressed = false;
  bool _isHovered = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 180),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.05).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    setState(() => _isPressed = true);
    _controller.forward();
  }

  void _handleTapUp(TapUpDetails details) {
    setState(() => _isPressed = false);
    _controller.reverse();
  }

  void _handleTapCancel() {
    setState(() => _isPressed = false);
    _controller.reverse();
  }

  void _handleHoverEnter() {
    setState(() => _isHovered = true);
    _controller.forward();
  }

  void _handleHoverExit() {
    setState(() => _isHovered = false);
    if (!_isPressed) {
      _controller.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isActive = _isPressed || _isHovered;
    
    return MouseRegion(
      onEnter: (_) => _handleHoverEnter(),
      onExit: (_) => _handleHoverExit(),
      child: GestureDetector(
        onTapDown: _handleTapDown,
        onTapUp: _handleTapUp,
        onTapCancel: _handleTapCancel,
        child: ScaleTransition(
          scale: _scaleAnimation,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOut,
            padding: EdgeInsets.symmetric(
              horizontal: isActive ? 20 : 18,
              vertical: isActive ? 14 : 12,
            ),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(isActive ? 0.3 : 0.25),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: Colors.white.withOpacity(isActive ? 0.4 : 0.3),
                width: isActive ? 1.5 : 1,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(isActive ? 0.15 : 0.1),
                  blurRadius: isActive ? 12 : 8,
                  offset: Offset(0, isActive ? 6 : 4),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  curve: Curves.easeOut,
                  padding: EdgeInsets.all(isActive ? 8 : 6),
        decoration: BoxDecoration(
                    color: Colors.white.withOpacity(isActive ? 0.4 : 0.3),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    Icons.rocket_launch,
                    color: Colors.white,
                    size: isActive ? 20 : 18,
                  ),
                ),
                const SizedBox(width: 12),
                Flexible(
                  child: Text(
                    'Ready to ace your placements!',
                    style: TextStyle(
          color: Colors.white,
                      fontSize: isActive ? 15 : 14,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.3,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// Staggered Animation Wrapper for Grid Items
class _AnimatedGridItem extends StatefulWidget {
  final Widget child;
  final int delay;

  const _AnimatedGridItem({
    required this.child,
    required this.delay,
  });

  @override
  State<_AnimatedGridItem> createState() => _AnimatedGridItemState();
}

class _AnimatedGridItemState extends State<_AnimatedGridItem>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.6, curve: Curves.easeOut),
      ),
    );

    _scaleAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.6, curve: Curves.easeOutBack),
      ),
    );

    Future.delayed(Duration(milliseconds: widget.delay), () {
      if (mounted) {
        _controller.forward();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: widget.child,
      ),
    );
  }
}

// Animated Feature Card with Pop Animation
class _AnimatedFeatureCard extends StatefulWidget {
  final String title;
  final IconData icon;
  final List<Color> gradientColors;
  final VoidCallback onTap;

  const _AnimatedFeatureCard({
    required this.title,
    required this.icon,
    required this.gradientColors,
    required this.onTap,
  });

  @override
  State<_AnimatedFeatureCard> createState() => _AnimatedFeatureCardState();
}

class _AnimatedFeatureCardState extends State<_AnimatedFeatureCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  bool _isPressed = false;
  bool _isHovered = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 180),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.08).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    setState(() => _isPressed = true);
    _controller.forward();
  }

  void _handleTapUp(TapUpDetails details) {
    setState(() => _isPressed = false);
    _controller.reverse();
    Future.delayed(const Duration(milliseconds: 150), () {
      if (mounted) {
        widget.onTap();
      }
    });
  }

  void _handleTapCancel() {
    setState(() => _isPressed = false);
    _controller.reverse();
  }

  void _handleHoverEnter() {
    setState(() => _isHovered = true);
    _controller.forward();
  }

  void _handleHoverExit() {
    setState(() => _isHovered = false);
    if (!_isPressed) {
      _controller.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isActive = _isPressed || _isHovered;
    
    return MouseRegion(
      onEnter: (_) => _handleHoverEnter(),
      onExit: (_) => _handleHoverExit(),
      child: GestureDetector(
        onTapDown: _handleTapDown,
        onTapUp: _handleTapUp,
        onTapCancel: _handleTapCancel,
        child: ScaleTransition(
          scale: _scaleAnimation,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOut,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: widget.gradientColors,
              ),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: widget.gradientColors[0].withOpacity(isActive ? 0.5 : 0.4),
                  blurRadius: isActive ? 25 : 20,
                  offset: Offset(0, isActive ? 12 : 10),
                  spreadRadius: isActive ? 3 : 2,
                ),
              ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
                AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  curve: Curves.easeOut,
                  padding: EdgeInsets.all(isActive ? 20 : 18),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(isActive ? 0.3 : 0.25),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(isActive ? 0.15 : 0.1),
                        blurRadius: isActive ? 12 : 8,
                        offset: Offset(0, isActive ? 6 : 4),
                      ),
                    ],
                  ),
                  child: Icon(
                    widget.icon,
                    size: isActive ? 38 : 36,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  widget.title,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    shadows: [
                      Shadow(
                        color: Colors.black.withOpacity(0.2),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
