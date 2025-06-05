"""
Firebase Firestore adapter for Django models.
This module provides utilities to sync Django models with Firebase Firestore.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
import json
from datetime import datetime, date
from decimal import Decimal


class FirebaseManager:
    """Singleton manager for Firebase operations."""
    
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_firebase()
        return cls._instance
    
    @classmethod
    def _initialize_firebase(cls):
        """Initialize Firebase Admin SDK."""
        if not firebase_admin._apps:
            cred_path = os.path.join(settings.BASE_DIR, 'config/credentials.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # For environment-based credentials
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
        
        cls._db = firestore.client()
    
    @property
    def db(self):
        """Get Firestore database instance."""
        if self._db is None:
            self._initialize_firebase()
        return self._db


class FirebaseModelMixin:
    """Mixin to add Firebase synchronization to Django models."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._firebase = FirebaseManager()
    
    def to_firestore_dict(self):
        """Convert model instance to Firestore-compatible dictionary."""
        data = {}
        
        for field in self._meta.fields:
            value = getattr(self, field.name)
            
            # Handle different field types
            if value is None:
                data[field.name] = None
            elif isinstance(value, (datetime, date)):
                data[field.name] = value.isoformat()
            elif isinstance(value, Decimal):
                data[field.name] = float(value)
            elif isinstance(value, models.Model):
                # Foreign key - store the ID
                data[field.name] = value.pk if value else None
            elif isinstance(field, models.JSONField):
                data[field.name] = value if value else {}
            else:
                data[field.name] = value
        
        # Add metadata
        data['_model'] = self.__class__.__name__
        data['_updated_at'] = datetime.now().isoformat()
        
        return data
    
    def save_to_firestore(self):
        """Save model instance to Firestore."""
        collection_name = self._meta.model_name + 's'
        doc_ref = self._firebase.db.collection(collection_name).document(str(self.pk))
        doc_ref.set(self.to_firestore_dict())
    
    def delete_from_firestore(self):
        """Delete model instance from Firestore."""
        collection_name = self._meta.model_name + 's'
        doc_ref = self._firebase.db.collection(collection_name).document(str(self.pk))
        doc_ref.delete()
    
    @classmethod
    def get_from_firestore(cls, pk):
        """Get model instance from Firestore by primary key."""
        firebase = FirebaseManager()
        collection_name = cls._meta.model_name + 's'
        doc_ref = firebase.db.collection(collection_name).document(str(pk))
        doc = doc_ref.get()
        
        if doc.exists:
            return cls.from_firestore_dict(doc.to_dict())
        return None
    
    @classmethod
    def list_from_firestore(cls, filters=None, limit=None):
        """List model instances from Firestore with optional filters."""
        firebase = FirebaseManager()
        collection_name = cls._meta.model_name + 's'
        query = firebase.db.collection(collection_name)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                query = query.where(field, '==', value)
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        docs = query.stream()
        return [cls.from_firestore_dict(doc.to_dict()) for doc in docs]
    
    @classmethod
    def from_firestore_dict(cls, data):
        """Create model instance from Firestore dictionary."""
        # Remove metadata
        data.pop('_model', None)
        data.pop('_updated_at', None)
        
        # Handle datetime fields
        for field in cls._meta.fields:
            field_name = field.name
            if field_name in data and data[field_name]:
                if isinstance(field, (models.DateTimeField, models.DateField)):
                    if isinstance(data[field_name], str):
                        try:
                            data[field_name] = datetime.fromisoformat(data[field_name])
                        except:
                            pass
        
        return cls(**data)


def sync_to_firestore(sender, instance, **kwargs):
    """Signal handler to sync model changes to Firestore."""
    if hasattr(instance, 'save_to_firestore'):
        instance.save_to_firestore()


def delete_from_firestore(sender, instance, **kwargs):
    """Signal handler to delete from Firestore when model is deleted."""
    if hasattr(instance, 'delete_from_firestore'):
        instance.delete_from_firestore()


# Utility functions for direct Firestore operations
def save_to_firestore_collection(collection_name, doc_id, data):
    """Save data directly to a Firestore collection."""
    firebase = FirebaseManager()
    doc_ref = firebase.db.collection(collection_name).document(str(doc_id))
    doc_ref.set(data)


def get_from_firestore_collection(collection_name, doc_id):
    """Get data directly from a Firestore collection."""
    firebase = FirebaseManager()
    doc_ref = firebase.db.collection(collection_name).document(str(doc_id))
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None


def list_from_firestore_collection(collection_name, filters=None, limit=None):
    """List data from a Firestore collection with optional filters."""
    firebase = FirebaseManager()
    query = firebase.db.collection(collection_name)
    
    if filters:
        for field, value in filters.items():
            query = query.where(field, '==', value)
    
    if limit:
        query = query.limit(limit)
    
    return [doc.to_dict() for doc in query.stream()]