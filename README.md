# Smart-Placement-Assistant
An AI mobile application designed to support university students in their placement journey. It offers personalized job suggestions, real-time notifications, resume sharing, company insights, and a chatbot for peer interaction. 

<p>
  <strong>Smart Placement Assistant</strong> is a cross-platform Flutter-based mobile application integrated with Firebase and IoT (ESP32) to guide and assist university students in their placement journey. It serves as a career-focused companion that utilizes <strong>Artificial Intelligence (AI)</strong>, <strong>Machine Learning (ML)</strong>, <strong>Natural Language Processing (NLP)</strong>, and embedded systems to deliver a personalized and intelligent experience.
</p>

<h3>Key Objectives:</h3>
<ul>
  <li>Provide <strong>AI-driven personalized career guidance</strong> based on student skills, interests, and academic history.</li>
  <li>Centralize and display company-specific information, hiring criteria, and recruitment timelines using <strong>automated scraping and ML classification</strong>.</li>
  <li>Send intelligent reminders and alerts using Firebase and AI scheduling models.</li>
  <li>Enhance peer communication through in-app discussion and smart chatbot features.</li>
  <li>Use <strong>NLP algorithms</strong> to parse and understand resume content for profile suggestions.</li>
</ul>

<h3>Core Technologies:</h3>
<ul>
  <li><strong>Flutter:</strong> Cross-platform mobile app framework</li>
  <li><strong>Firebase:</strong> Backend services including Firestore, Auth, Cloud Functions, and Notifications</li>
  <li><strong>Python + Flask:</strong> Backend services for AI/NLP resume analysis and smart recommendations</li>
  <li><strong>Machine Learning:</strong> Skill–job matching, trend analysis, and company shortlisting logic</li>
  <li><strong>Web Scraping:</strong> Automatic extraction of company recruitment info from official sites</li>
</ul>
<h3>Who is it for?</h3>
<p>
  This platform is designed for <strong>university students and placement cells</strong> to help them stay prepared and informed throughout the placement season. It is flexible enough to support diverse academic streams and offers tailored advice based on real-time data.
</p>

<h3>Future Scope:</h3>
<ul>
  <li>Integrate <strong>resume scoring</strong> using AI-based feedback models</li>
  <li>Connect to external job boards like LinkedIn or Indeed using smart scraping + ML filtering</li>
  <li>Support offline caching and progressive web app (PWA) version</li>
  <li>Build a web-based <strong>TPO dashboard</strong> for event and data management</li>
</ul>

<h2> Features</h2>
<ul>
  <li><strong>AI-Powered Career Suggestions:</strong> Uses NLP and ML to analyze student profiles and recommend suitable job roles or companies.</li>
  <li><strong>Company Information Dashboard:</strong> Scrapes official company websites to present relevant info like eligibility, roles offered, CTC, and deadlines.</li>
  <li><strong>Smart Calendar Integration:</strong> Automatically adds placement events, deadlines, and reminders to a unified calendar.</li>
  <li><strong>Resume Upload & Preview:</strong> Upload resume in PDF format and preview it within the app.</li>
  <li><strong>Student Discussion Forum:</strong> Peer-to-peer discussion chat system for interview tips, resources, and doubts.</li>
  <li><strong>Firebase-Backed Authentication:</strong> Secure sign-up and login using Firebase Auth.</li>
  <li><strong>Push Notifications:</strong> For interview schedules, reminders, announcements, and company updates.</li>
</ul>

<h2>Installation Instructions</h2>
<ol>
  <li><strong>Clone the Repository:</strong><br>
    <code>git clone https://github.com/yourusername/smart_placement_assistant.git</code>
  </li>
  <li><strong>Navigate to the Project Directory:</strong><br>
    <code>cd smart_placement_assistant</code>
  </li>
  <li><strong>Install Dependencies:</strong><br>
    <code>flutter pub get</code>
  </li>
  <li><strong>Configure Firebase:</strong><br>
    - Add your <code>google-services.json</code> file to <code>android/app/</code><br>
    - Ensure Firebase project is correctly connected to your app (Firebase Console → Project Settings)
  </li>
  <li><strong>Run the App:</strong><br>
    <code>flutter run</code><br>
    Or connect your Android device/emulator before running.
  </li>
</ol>



