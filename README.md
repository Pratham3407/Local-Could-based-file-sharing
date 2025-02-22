Cloud-Based Secure File Sharing

A secure, temporary file-sharing web application built using Flask, JavaScript, and QR codes. Users can upload files, generate password-protected shareable links, and access them via QR codes. To enhance security, files automatically expire and delete after a set duration.

Features:

✅ Secure file upload with password protection
✅ Temporary shareable links with auto-expiration
✅ QR code generation for easy access 
✅ Automatic file deletion after 5 minutes for privacy

Tech Stack:

Backend: Flask (Python)
Frontend: HTML, CSS, JavaScript
Security: Password-protected access, QR authentication

Installation & Setup:
Prerequisites
Ensure you have the following installed:

1. Python 3.x
2. Flask
3. Required dependencies from requirements.txt

Installation Steps:
1. Clone the Repository
2. Install Dependencies
3. pip install -r requirements.txt
4. Run the Application using
python app.py      
5. Open http://localhost:5000/ in your browser.

How It Works: 

Users upload files via the web interface.
The system generates a unique link, password, and QR code.
Files can be accessed using the provided credentials.
After 5 minutes, files and QR codes are automatically deleted.

Cloud Computing Paradigm:

This project follows the Software as a Service (SaaS) model, providing a web-based solution for secure file sharing. It leverages cloud computing principles such as on-demand access, resource scalability, and security.
