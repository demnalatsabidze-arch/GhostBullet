import os
import time
import subprocess
import signal
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker
from stem.control import Controller
import stat

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ghost_bullet.db')
TOR_KEYS_DIR = '/tor_keys'
TORRC_PATH = '/etc/tor/torrc'
SITES_CONTENT_DIR = '/sites_content'
TOR_CONTROL_PORT = 9051
TOR_PASSWORD = 'password' # For local docker bridge only

# DB Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

# Wait for tables to be created by UI
print("[TorManager] Waiting for UI to initialize DB tables...")
while True:
    try:
        metadata.reflect(bind=engine)
        if 'sites' in metadata.tables:
            break
    except Exception:
        pass
    time.sleep(2)
print("[TorManager] DB tables found.")

Base = declarative_base(metadata=metadata)

# Define Site class mapping to existing table
class Site(Base):
    __table__ = metadata.tables['sites']

def generate_torrc(sites):
    """Generates the torrc file based on deployed sites."""
    torrc_content = f"""
SocksPort 0
ControlPort {TOR_CONTROL_PORT}
CookieAuthentication 1
# Optionally set hashed control password
# HashedControlPassword ...
"""
    
    for site in sites:
        if site.is_deployed and site.status != 'generating_vanity':
            site_dir = os.path.join(TOR_KEYS_DIR, site.id)
            
            # Ensure dir exists with correct permissions
            if not os.path.exists(site_dir):
                os.makedirs(site_dir, mode=0o700)
            
            # Always ensure correct ownership and permissions for the directory and its contents
            try:
                tor_uid = pwd.getpwnam("debian-tor").pw_uid
                tor_gid = pwd.getpwnam("debian-tor").pw_gid
                os.chown(site_dir, tor_uid, tor_gid)
                os.chmod(site_dir, 0o700)
                
                for filename in os.listdir(site_dir):
                    filepath = os.path.join(site_dir, filename)
                    os.chown(filepath, tor_uid, tor_gid)
                    os.chmod(filepath, 0o600)
            except Exception as e:
                print(f"[TorManager] Error fixing permissions for {site_dir}: {e}")
                
                
            torrc_content += f"\n# Site: {site.name}\n"
            torrc_content += f"HiddenServiceDir {site_dir}\n"
            torrc_content += f"HiddenServiceVersion 3\n"
            torrc_content += f"HiddenServicePort 80 {site.target_host}:{site.target_port}\n"
            
    with open(TORRC_PATH, 'w') as f:
        f.write(torrc_content)
    
    # Fix permissions for torrc
    os.chmod(TORRC_PATH, 0o644)

def reload_tor():
    """Tells Tor to reload its configuration via Stem."""
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate()  # Uses cookie auth
            controller.signal(signal.SIGHUP)
            return True
    except Exception as e:
        print(f"Error reloading Tor via Stem: {e}")
        # Fallback to shell sighup if stem fails
        try:
            pid = int(subprocess.check_output(["pidof", "tor"]).strip())
            os.kill(pid, signal.SIGHUP)
            return True
        except Exception as e2:
            print(f"Error reloading Tor via shell: {e2}")
            return False

def sync_all():
    db = SessionLocal()
    try:
        sites = db.query(Site).all()
        
        # Check if torrc needs update
        # For simplicity in this demo, we'll rewrite and reload if there are changes.
        # To make it efficient, we keep track of the last applied state.
        
        needs_reload = False
        
        for site in sites:
            # If site is deployed but waiting for tor to create keys
            if site.is_deployed and site.status == 'starting':
                site_dir = os.path.join(TOR_KEYS_DIR, site.id)
                hostname_file = os.path.join(site_dir, 'hostname')
                
                # If Tor has created the hostname, update the DB
                if os.path.exists(hostname_file):
                    with open(hostname_file, 'r') as f:
                        hostname = f.read().strip()
                        if hostname and (site.onion_address != hostname or site.status == 'starting'):
                            site.onion_address = hostname
                            site.status = 'running'
                            print(f"[TorManager] Site {site.name} mapped to {hostname}")
                            needs_reload = True # Force sync to catch this state
                            
                            # CREATE SYMLINK FOR BUILT-IN NGINX HOSTING
                            if site.is_builtin:
                                site_content_dir = os.path.join(SITES_CONTENT_DIR, str(site.id))
                                symlink_path = os.path.join(SITES_CONTENT_DIR, hostname)
                                # Only link if the content dir actually exists
                                if os.path.exists(site_content_dir):
                                    if os.path.exists(symlink_path) or os.path.islink(symlink_path):
                                        os.remove(symlink_path)
                                    os.symlink(str(site.id), symlink_path)
                                    print(f"[TorManager] Created symlink for Nginx: {hostname} -> {site.id}")
                else:
                    # Hostname not there yet, torrc might need it.
                    needs_reload = True
                    
            elif site.is_deployed and site.status == 'running':
                # Sanity check: does hostname still exist?
                site_dir = os.path.join(TOR_KEYS_DIR, site.id)
                if not os.path.exists(os.path.join(site_dir, 'hostname')):
                    print(f"[TorManager] Keys missing for {site.name}, changing status.")
                    site.status = 'starting'
                    site.onion_address = None
                    needs_reload = True
                else:
                    # Persistent symlink assertion for Nginx
                    if site.is_builtin and site.onion_address:
                        site_content_dir = os.path.join(SITES_CONTENT_DIR, str(site.id))
                        symlink_path = os.path.join(SITES_CONTENT_DIR, site.onion_address)
                        if os.path.exists(site_content_dir):
                            if not (os.path.exists(symlink_path) or os.path.islink(symlink_path)):
                                os.symlink(str(site.id), symlink_path)
                                print(f"[TorManager] Restored symlink for Nginx: {site.onion_address} -> {site.id}")
                    
            elif not site.is_deployed and site.status != 'stopped':
                site.status = 'stopped'
                
                # REMOVE SYMLINK FOR BUILTIN HOSTING
                if site.is_builtin and site.onion_address:
                    symlink_path = os.path.join(SITES_CONTENT_DIR, site.onion_address)
                    if os.path.islink(symlink_path):
                        os.remove(symlink_path)
                        print(f"[TorManager] Removed symlink for Nginx: {site.onion_address}")
                        
                needs_reload = True

        # Write config and reload if Tor isn't running or config changed
        generate_torrc(sites)
            
        if needs_reload:
            res = reload_tor()
            if res:
                print("[TorManager] Reloaded Tor config successfully.")
            
        db.commit()
    except Exception as e:
        print(f"[TorManager] Error in sync task: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import pwd # Import here to ensure it works on correct OS
    
    print("[TorManager] Starting local Tor process...")
    # Change owner of required directories
    os.system(f'chown -R debian-tor:debian-tor /tor_keys /etc/tor /var/lib/tor')
    
    # Initialize basic torrc
    with open(TORRC_PATH, 'w') as f:
        f.write(f"SocksPort 0\nControlPort {TOR_CONTROL_PORT}\nCookieAuthentication 1\n")
    os.chmod(TORRC_PATH, 0o644)

    # Start Tor as daemon user with valid shell
    tor_proc = subprocess.Popen(["su", "-s", "/bin/sh", "debian-tor", "-c", f"exec tor -f {TORRC_PATH}"])
    
    print("[TorManager] Tor process started. Beginning sync loop...")
    time.sleep(2) # Give Tor time to spin up control port
    
    while True:
        sync_all()
        time.sleep(10) # Poll every 10 seconds
