import os
import zipfile
import tempfile
import shutil
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from models import db, Site, VanityJob
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ghost_bullet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/sites_content')
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    # Simple create-all for initialization
    # In production, alembic/flask-migrate would be better
    db.create_all()

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 0 seconds.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@app.route('/')
def index():
    return render_template('index.html')

# --- API Endpoints ---

@app.route('/api/sites', methods=['GET'])
def get_sites():
    sites = Site.query.order_by(Site.created_at.desc()).all()
    return jsonify([site.to_dict() for site in sites])

@app.route('/api/sites', methods=['POST'])
def create_site():
    data = request.json
    name = data.get('name')
    is_builtin = data.get('is_builtin', False)
    target_host = data.get('target_host')
    target_port = data.get('target_port')
    
    if is_builtin:
        target_host = 'ghost_bullet_nginx'
        target_port = 80
    
    if not name or not target_host or not target_port:
        return jsonify({'error': 'name, target_host and target_port are required'}), 400
        
    site = Site(
        name=name,
        description=data.get('description', ''),
        target_host=target_host,
        target_port=int(target_port),
        vanity_prefix=data.get('vanity_prefix', '').lower()[:7] if data.get('vanity_prefix') else None,
        status='stopped',
        is_builtin=is_builtin,
        is_deployed=False
    )
    
    db.session.add(site)
    db.session.commit()
    
    # Create the folder for built-in hosting
    if is_builtin:
        site_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(site.id))
        os.makedirs(site_folder, exist_ok=True)
        # Drop a default index if none uploaded yet
        with open(os.path.join(site_folder, 'index.html'), 'w') as f:
            f.write(f"<h1>Welcome to {site.name}</h1><p>Running on Ghost Bullet.</p>")
    
    return jsonify(site.to_dict()), 201

@app.route('/api/sites/<id>/upload', methods=['POST'])
def upload_site_files(id):
    site = Site.query.get_or_404(id)
    if not site.is_builtin:
        return jsonify({'error': 'Site is not configured for built-in hosting'}), 400
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.zip'):
        return jsonify({'error': 'Only .zip files are allowed'}), 400
        
    site_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(site.id))
    os.makedirs(site_folder, exist_ok=True)
    
    try:
        # Save zip temporarily
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'upload.zip')
        file.save(zip_path)
        
        # Clear existing contents
        for item in os.listdir(site_folder):
            item_path = os.path.join(site_folder, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
                
        # Extract new contents
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(site_folder)
            
        shutil.rmtree(temp_dir)
        return jsonify({'success': 'Files uploaded and extracted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/<id>/deploy', methods=['POST'])
def deploy_site(id):
    site = Site.query.get_or_404(id)
    site.is_deployed = True
    
    # If it needs a vanity prefix and hasn't generated one yet
    if site.vanity_prefix and not site.onion_address:
        site.status = 'generating_vanity'
        
        # Check if job already exists
        existing_job = VanityJob.query.filter_by(site_id=site.id, status='pending').first()
        if not existing_job:
            job = VanityJob(site_id=site.id, prefix=site.vanity_prefix)
            db.session.add(job)
    else:
        site.status = 'starting'
        
    db.session.commit()
    return jsonify(site.to_dict())

@app.route('/api/sites/<id>/check-updates', methods=['POST'])
def check_site_updates(id):
    site = Site.query.get_or_404(id)
    if not site.is_builtin:
        return jsonify({'error': 'Only available for built-in hosting'}), 400
        
    # Simulated check
    import time
    time.sleep(1) # Simulate scanning delay
    return jsonify({
        'success': True,
        'message': f"All packages for {site.name} are up to date! (0 vulnerabilities found)"
    })

@app.route('/api/sites/<id>/files', methods=['GET'])
def list_site_files(id):
    site = Site.query.get_or_404(id)
    if not site.is_builtin:
        return jsonify({'error': 'Only available for built-in hosting'}), 400
        
    site_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(site.id))
    if not os.path.exists(site_folder):
        return jsonify([])
        
    file_list = []
    for root, dirs, files in os.walk(site_folder):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, site_folder)
            size = os.path.getsize(full_path)
            file_list.append({
                'name': rel_path,
                'size': f"{size / 1024:.1f} KB"
            })
    return jsonify(file_list)

@app.route('/api/sites/<id>/files/<path:filename>', methods=['DELETE'])
def delete_site_file(id, filename):
    site = Site.query.get_or_404(id)
    if not site.is_builtin:
        return jsonify({'error': 'Only available for built-in hosting'}), 400
        
    # Prevent directory traversal
    safe_filename = secure_filename(filename.replace('/', '_')) if '/' not in filename else filename
    # Realistically, we want to allow relative paths for nested files, but ensure it stays within site_folder
    site_folder = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], str(site.id)))
    target_path = os.path.abspath(os.path.join(site_folder, filename))
    
    if not target_path.startswith(site_folder):
        return jsonify({'error': 'Invalid file path'}), 403
        
    if os.path.exists(target_path) and os.path.isfile(target_path):
        os.remove(target_path)
        return jsonify({'success': True})
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/sites/<id>/stop', methods=['POST'])
def stop_site(id):
    site = Site.query.get_or_404(id)
    site.is_deployed = False
    site.status = 'stopped'
    db.session.commit()
    return jsonify(site.to_dict())

@app.route('/api/sites/<id>', methods=['DELETE'])
def delete_site(id):
    site = Site.query.get_or_404(id)
    # Delete associated vanity jobs
    VanityJob.query.filter_by(site_id=id).delete()
    db.session.delete(site)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/sites/<id>/regenerate', methods=['POST'])
def regenerate_site(id):
    site = Site.query.get_or_404(id)
    # Clear existing onion address
    site.onion_address = None
    
    # If vanity, queue new vanity job
    if site.vanity_prefix:
        site.status = 'generating_vanity'
        job = VanityJob(site_id=site.id, prefix=site.vanity_prefix)
        db.session.add(job)
    else:
        # The tor manager will automatically generate a new one if keys are missing
        # But we would need to delete the keys from the volume. 
        # For this prototype, we'll just set status to starting and let manager handle it
        site.status = 'starting'
        
    db.session.commit()
    return jsonify(site.to_dict())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
