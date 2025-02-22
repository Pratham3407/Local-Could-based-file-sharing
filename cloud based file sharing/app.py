import os
import random
import string
import zipfile
import threading
import time
import qrcode
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, send_file, jsonify
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For flash messages
UPLOAD_FOLDER = 'uploads'
QR_FOLDER = 'static/qrcodes'  # New folder for QR codes
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2 GB file size limit

# Dictionary to store file details: {link_id: {file_list, password, timestamp}}
file_data = {}

# Ensure upload and QR folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

def generate_random_string(length=8):
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_qr_code(url, link_id):
    """Generate a QR code for the given URL and save it."""
    qr = qrcode.make(url)
    qr_path = os.path.join(QR_FOLDER, f"{link_id}.png")
    qr.save(qr_path)
    return qr_path

def delete_files_and_link(link_id):
    """Delete files, link, and QR code after the expiration time."""
    time.sleep(300)  # 300 seconds (5 minutes)
    if link_id in file_data:
        for file in file_data[link_id]['files']:
            file_path = os.path.join(UPLOAD_FOLDER, file)
            if os.path.exists(file_path):
                os.remove(file_path)

        # Remove QR code file
        qr_path = os.path.join(QR_FOLDER, f"{link_id}.png")
        if os.path.exists(qr_path):
            os.remove(qr_path)

        del file_data[link_id]

@app.route('/')
def upload_page():
    """Render the file upload page with optional success message."""
    share_link = request.args.get('share_link')
    password = request.args.get('password')
    expiration = request.args.get('expiration')
    qr_code = request.args.get('qr_code')
    return render_template('upload.html', share_link=share_link, password=password, expiration=expiration, qr_code=qr_code)

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle multiple file uploads."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files selected.'}), 400
# extracts files from /upload request 
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files selected.'}), 400
# checks for the file size (should not exceed 2GB)
    total_size = sum(len(file.read()) for file in files)
    for file in files:
        file.seek(0)  # Reset file pointer after checking size

    if total_size > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({'error': 'Total upload size cannot exceed 2GB'}), 400
# save the files in the /uploads folder
    uploaded_files = []
    for file in files:
        if file.filename == '':
            continue
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        uploaded_files.append(filename)

    # Generate unique link and password
    link_id = generate_random_string(10)
    password = generate_random_string()

    # Store file details
    file_data[link_id] = {'files': uploaded_files, 'password': password, 'timestamp': time.time()}

    # Generate QR code
    share_link = request.url_root + 'file/' + link_id
    qr_path = generate_qr_code(share_link, link_id)

    # Start background thread to delete the files, link, and QR code after expiration time
    # note: to change the 5 min timer, change the value of 300 to required seconds & also in the delete_files_and_link function as well as in upload.html (js part), also on line 120.
    threading.Thread(target=delete_files_and_link, args=(link_id,), daemon=True).start()

    expiration_time = time.time() + 300  # 300 seconds (5 minutes)
    return jsonify({
        'share_link': share_link,
        'password': password,
        'expiration': expiration_time,
        'qr_code': '/' + qr_path  # Return QR Code URL
    })

@app.route('/file/<link_id>', methods=['GET', 'POST'])
def access_file(link_id):
    """Serve the password page and validate access."""
    file_info = file_data.get(link_id) # check if the link is valid or not

    if not file_info:
        flash('Invalid or expired link.')
        return redirect(url_for('upload_page'))

    if time.time() - file_info['timestamp'] > 300: # here also change the value of 300 to required seconds
        delete_files_and_link(link_id)
        flash('Link has expired.')
        return redirect(url_for('upload_page'))
# veruify the password from password.html form
    if request.method == 'POST':
        entered_password = request.form['password'].strip()
        stored_password = file_info['password']
        if entered_password == stored_password:
            return render_template('file_list.html', files=file_info['files'], link_id=link_id)
        else:
            flash('Incorrect password. Please try again.')
            return redirect(url_for('access_file', link_id=link_id))

    return render_template('password.html', link_id=link_id)

@app.route('/qr/<link_id>')
def get_qr_code(link_id):
    """Serve the QR code image."""
    qr_path = os.path.join(QR_FOLDER, f"{link_id}.png")
    if os.path.exists(qr_path):
        return send_from_directory(QR_FOLDER, f"{link_id}.png")
    else:
        flash('QR code not found or expired.')
        return redirect(url_for('upload_page'))

@app.route('/download/<link_id>/<filename>')
def download_file(link_id, filename):
    """Download a single file."""
    file_info = file_data.get(link_id)
    if not file_info or filename not in file_info['files']:
        flash('File not found.')
        return redirect(url_for('upload_page'))

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/download_selected/<link_id>', methods=['POST'])
def download_selected_files(link_id):
    """Download selected files as a zip."""
    file_info = file_data.get(link_id)
    if not file_info:
        flash('Invalid or expired link.')
        return redirect(url_for('upload_page'))

    selected_files = request.form.getlist('files_to_download')
    if selected_files:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_name in selected_files:
                file_path = os.path.join(UPLOAD_FOLDER, file_name)
                zip_file.write(file_path, arcname=file_name)
        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True, download_name=f"{link_id}_files.zip", mimetype="application/zip")
    else:
        flash('No files selected for download.')
        return redirect(url_for('access_file', link_id=link_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
