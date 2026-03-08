from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime

db = SQLAlchemy()

class Site(db.Model):
    __tablename__ = 'sites'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_host = db.Column(db.String(255), nullable=False)
    target_port = db.Column(db.Integer, nullable=False)
    
    # tor specific
    onion_address = db.Column(db.String(255), nullable=True)
    vanity_prefix = db.Column(db.String(7), nullable=True)
    
    # status: 'stopped', 'starting', 'running', 'generating_vanity', 'error'
    status = db.Column(db.String(50), default='stopped') 
    
    # Built-in Nginx Hosting Flag
    is_builtin = db.Column(db.Boolean, default=False)
    
    # Internal boolean to tell the Tor manager if this should be actively mapped in torrc
    is_deployed = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_host': self.target_host,
            'target_port': self.target_port,
            'onion_address': self.onion_address,
            'vanity_prefix': self.vanity_prefix,
            'status': self.status,
            'is_builtin': self.is_builtin,
            'is_deployed': self.is_deployed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class VanityJob(db.Model):
    __tablename__ = 'vanity_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = db.Column(db.String(36), db.ForeignKey('sites.id'), nullable=False)
    prefix = db.Column(db.String(7), nullable=False)
    
    # status: 'pending', 'processing', 'completed', 'failed'
    status = db.Column(db.String(50), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
