import os
import time
import subprocess
import shutil
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ghost_bullet.db')
TOR_KEYS_DIR = '/tor_keys'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

print("[VanityWorker] Waiting for UI to initialize DB tables...")
while True:
    try:
        metadata.reflect(bind=engine)
        if 'vanity_jobs' in metadata.tables and 'sites' in metadata.tables:
            break
    except Exception:
        pass
    time.sleep(2)
print("[VanityWorker] DB tables found.")

Base = declarative_base(metadata=metadata)

# Define models mapped to existing tables
class VanityJob(Base):
    __table__ = metadata.tables['vanity_jobs']

class Site(Base):
    __table__ = metadata.tables['sites']

def generate_vanity(job, site):
    prefix = job.prefix.lower()
    print(f"[VanityWorker] Starting generation for prefix: {prefix}")
    
    # We output to a temporary directory
    temp_dir = f"/tmp/vanity_{job.id}"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # mkp224o -d <output_dir> -n 1 <prefix>
    # -n 1 means generate only 1 address
    cmd = ["mkp224o", "-d", temp_dir, "-n", "1", prefix]
    
    try:
        # For long prefixes, this can take a while, so we use subprocess
        # NOTE: 7 chars can take a long time on slow hardware. Caution is advised.
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        # Check the temporary directory for the generated result
        generated_dirs = [d for d in os.listdir(temp_dir) if d.endswith('.onion')]
        
        if not generated_dirs:
            print(f"[VanityWorker] Failed to generate keys for {prefix}: {stderr.decode()}")
            job.status = 'failed'
            # site.status = 'error'
            return False
            
        result_dir = os.path.join(temp_dir, generated_dirs[0])
        
        # We need to copy these to /tor_keys/<site_id>/
        site_keys_dir = os.path.join(TOR_KEYS_DIR, site.id)
        if not os.path.exists(site_keys_dir):
            os.makedirs(site_keys_dir, mode=0o700)
            
        # Copy hostname, hs_ed25519_public_key, hs_ed25519_secret_key
        for f in ['hostname', 'hs_ed25519_public_key', 'hs_ed25519_secret_key']:
            src = os.path.join(result_dir, f)
            dst = os.path.join(site_keys_dir, f)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                os.chmod(dst, 0o600)
        
        # Note: Tor Manager runs as debian-tor (id usually 100-something inside default image).
        # Docker handles volume permissions decently if set up right, but we may need to chown.
        # Since we mapped tor_keys_vol as root or standard, we rely on Tor Manager to fix permissions on its next sync loop.
                
        print(f"[VanityWorker] Successfully generated {generated_dirs[0]} for site {site.name}")
        job.status = 'completed'
        
        # We don't need to manually update site.onion_address here;
        # Tor Manager observes the hostname file on disk and will sync it and reload Tor.
        # But we could set it to "starting" so it knows it should pick it up.
        site.status = 'starting'
        
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"[VanityWorker] Error running mkp224o: {e}")
        job.status = 'failed'
        return False

def check_queue():
    db = SessionLocal()
    try:
        # Find exactly one pending job to work on
        job = db.query(VanityJob).filter(VanityJob.status == 'pending').first()
        
        if job:
            site = db.query(Site).filter(Site.id == job.site_id).first()
            if not site:
                print(f"[VanityWorker] Site {job.site_id} not found for job {job.id}")
                job.status = 'failed'
                db.commit()
                return
                
            job.status = 'processing'
            db.commit()
            
            generate_vanity(job, site)
            db.commit()
    except Exception as e:
        print(f"[VanityWorker] Error in queue check: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("[VanityWorker] Starting job polling...")
    while True:
        check_queue()
        time.sleep(5) # Poll every 5 seconds
