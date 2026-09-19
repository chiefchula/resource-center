from datetime import datetime
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


# ---------- Enums ----------
class ItemStatus(str, Enum):
    ACTIVE = 'active'
    DECOMMISSIONED = 'decommissioned'
    PENDING_TRANSFER = 'pending_transfer'
    IN_TRANSIT = 'in_transit'


class TransferStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class AcquisitionType(str, Enum):
    DONATED = 'donated'
    PURCHASED = 'purchased'


# ---------- Models ----------
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    resource_center_id = db.Column(db.Integer, db.ForeignKey('resource_centers.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resource_center = db.relationship('ResourceCenter', backref='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# class ResourceCenter(db.Model):
#     __tablename__ = 'resource_centers'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False)
#     location = db.Column(db.String(200))
#     contact_person = db.Column(db.String(120))
#     contact_email = db.Column(db.String(120))
#     contact_phone = db.Column(db.String(30))
#     is_active = db.Column(db.Boolean, default=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     items = db.relationship('Item', backref='current_center', lazy=True,
#                             foreign_keys='Item.current_center_id')

#     def __repr__(self):
#         return f'<ResourceCenter {self.name}>'

class ResourceCenter(db.Model):
    __tablename__ = 'resource_centers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    # Administrative location
    subcounty = db.Column(db.String(120))
    ward = db.Column(db.String(120))
    location = db.Column(db.String(200))  # free-text description/address

    # Geolocation (optional — can be filled later)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    contact_person = db.Column(db.String(120))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('Item', backref='current_center', lazy=True,
                            foreign_keys='Item.current_center_id')

    @property
    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    def __repr__(self):
        return f'<ResourceCenter {self.name}>'



class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(120))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    donated_items = db.relationship('Item', backref='donor_organization', lazy=True)

    def __repr__(self):
        return f'<Organization {self.name}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.Text)

    items = db.relationship('Item', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    serial_number = db.Column(db.String(120), unique=True)
    quantity = db.Column(db.Integer, default=1)
    condition = db.Column(db.String(50))

    # Acquisition
    acquisition_type = db.Column(db.String(20), nullable=False)  # donated / purchased
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    purchase_price = db.Column(db.Float)
    purchase_date = db.Column(db.DateTime)

    # Location & handling
    current_center_id = db.Column(db.Integer, db.ForeignKey('resource_centers.id'), nullable=False)
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    received_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Status
    status = db.Column(db.String(30), default=ItemStatus.ACTIVE.value)
    decommission_date = db.Column(db.DateTime)
    decommission_reason = db.Column(db.Text)
    decommissioned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    receiver = db.relationship('User', foreign_keys=[received_by_id])
    decommissioned_by = db.relationship('User', foreign_keys=[decommissioned_by_id])
    transfers = db.relationship('Transfer', backref='item', lazy=True,
                                cascade='all, delete-orphan')

    @property
    def is_active(self):
        return self.status == ItemStatus.ACTIVE.value

    @property
    def is_decommissioned(self):
        return self.status == ItemStatus.DECOMMISSIONED.value

    def __repr__(self):
        return f'<Item {self.name}>'


class Transfer(db.Model):
    __tablename__ = 'transfers'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    from_center_id = db.Column(db.Integer, db.ForeignKey('resource_centers.id'), nullable=False)
    to_center_id = db.Column(db.Integer, db.ForeignKey('resource_centers.id'), nullable=False)

    status = db.Column(db.String(30), default=TransferStatus.PENDING.value)
    sent_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sent_date = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_date = db.Column(db.DateTime)
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    received_date = db.Column(db.DateTime)

    notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)

    from_center = db.relationship('ResourceCenter', foreign_keys=[from_center_id])
    to_center = db.relationship('ResourceCenter', foreign_keys=[to_center_id])
    sender = db.relationship('User', foreign_keys=[sent_by_id])
    approver = db.relationship('User', foreign_keys=[approved_by_id])
    receiver = db.relationship('User', foreign_keys=[received_by_id])

    def __repr__(self):
        return f'<Transfer item={self.item_id} {self.status}>'