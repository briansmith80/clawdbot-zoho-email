#!/usr/bin/env python3
"""
Tests for Zoho Webhook Handler

Run with: python -m pytest tests/test_webhook_handler.py -v
"""

import os
import json
import tempfile
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Import the modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from zoho_webhook_handler import (
    ZohoWebhookPayload,
    ProcessedEvent,
    WebhookDatabase,
    ZohoWebhookVerifier,
    ZohoWebhookHandler,
    LoggingEventDelivery,
    EventDelivery,
)


class TestWebhookDatabase:
    """Tests for the WebhookDatabase class."""
    
    def setup_method(self):
        """Create a temporary database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = WebhookDatabase(self.temp_db.name)
    
    def teardown_method(self):
        """Clean up temporary database."""
        os.unlink(self.temp_db.name)
    
    def test_init_creates_tables(self):
        """Test that database initialization creates required tables."""
        assert os.path.exists(self.temp_db.name)
    
    def test_is_processed_false_for_new_event(self):
        """Test that new events return False for is_processed."""
        result = self.db.is_processed("account1", "msg1", "hash1")
        assert result is False
    
    def test_mark_processed_then_is_processed_true(self):
        """Test that marking an event processed makes is_processed return True."""
        event = ProcessedEvent(
            account_id="account1",
            message_id="msg1",
            event_hash="hash1",
            processed_at=datetime.now(),
            folder_id="INBOX"
        )
        self.db.mark_processed(event)
        
        result = self.db.is_processed("account1", "msg1", "hash1")
        assert result is True
    
    def test_different_hash_not_processed(self):
        """Test that different hash for same account/message is not considered processed."""
        event = ProcessedEvent(
            account_id="account1",
            message_id="msg1",
            event_hash="hash1",
            processed_at=datetime.now(),
            folder_id="INBOX"
        )
        self.db.mark_processed(event)
        
        result = self.db.is_processed("account1", "msg1", "hash2")
        assert result is False
    
    def test_cleanup_old_events(self):
        """Test cleanup of old events."""
        old_event = ProcessedEvent(
            account_id="account1",
            message_id="old_msg",
            event_hash="old_hash",
            processed_at=datetime.now() - timedelta(days=45),
            folder_id="INBOX"
        )
        self.db.mark_processed(old_event)
        
        recent_event = ProcessedEvent(
            account_id="account1",
            message_id="recent_msg",
            event_hash="recent_hash",
            processed_at=datetime.now(),
            folder_id="INBOX"
        )
        self.db.mark_processed(recent_event)
        
        removed = self.db.cleanup_old_events(days=30)
        
        assert removed == 1
        assert self.db.is_processed("account1", "recent_msg", "recent_hash") is True
        assert self.db.is_processed("account1", "old_msg", "old_hash") is False


class TestZohoWebhookVerifier:
    """Tests for the ZohoWebhookVerifier class."""
    
    def setup_method(self):
        """Set up verifier with known secret."""
        self.secret = "test-webhook-secret"
        self.verifier = ZohoWebhookVerifier(self.secret)
    
    def test_verify_valid_signature(self):
        """Test verification of a valid signature."""
        payload = b'{"account_id": "test", "message_id": "123"}'
        computed_hmac = hmac.new(self.secret.encode('utf-8'), payload, hashlib.sha256)
        signature = base64.b64encode(computed_hmac.digest()).decode('utf-8')
        
        result = self.verifier.verify_signature(payload, signature)
        assert result is True
    
    def test_verify_invalid_signature(self):
        """Test rejection of invalid signature."""
        payload = b'{"account_id": "test", "message_id": "123"}'
        signature = "invalid_signature"
        
        result = self.verifier.verify_signature(payload, signature)
        assert result is False
    
    def test_verify_empty_signature(self):
        """Test rejection of empty signature."""
        payload = b'{"account_id": "test", "message_id": "123"}'
        signature = ""
        
        result = self.verifier.verify_signature(payload, signature)
        assert result is False
    
    def test_verify_with_sha256_prefix_rejected(self):
        """Test that sha256= prefix is rejected (Zoho doesn't use it)."""
        payload = b'{"account_id": "test", "message_id": "123"}'
        computed_hmac = hmac.new(self.secret.encode('utf-8'), payload, hashlib.sha256)
        signature = base64.b64encode(computed_hmac.digest()).decode('utf-8')
        signature_with_prefix = f"sha256={signature}"
        
        result = self.verifier.verify_signature(payload, signature_with_prefix)
        assert result is False


class TestZohoWebhookHandler:
    """Tests for the ZohoWebhookHandler class."""
    
    def setup_method(self):
        """Set up handler with test configuration."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.config = {
            'db_path': self.temp_db.name,
            'max_payload_size': 1024 * 1024,
            'enabled_accounts': ['account1', 'account2'],
            'secrets': {
                'account1': 'secret1',
                'account2': 'secret2'
            },
        }
        self.handler = ZohoWebhookHandler(self.config)
    
    def teardown_method(self):
        """Clean up temporary files."""
        os.unlink(self.temp_db.name)
    
    def test_parse_valid_payload(self):
        """Test parsing a valid webhook payload."""
        raw_payload = {
            'account_id': 'account1',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        
        result = self.handler.parse_payload(raw_payload)
        
        assert result is not None
        assert result.account_id == 'account1'
        assert result.message_id == 'msg123'
        assert result.folder_id == 'INBOX'
        assert result.event_type == 'new_mail'
        assert result.timestamp == 1234567890
    
    def test_parse_payload_missing_required_fields(self):
        """Test parsing fails for missing required fields."""
        raw_payload = {
            'folder_id': 'INBOX',
            'event_type': 'new_mail'
        }
        
        result = self.handler.parse_payload(raw_payload)
        assert result is None
    
    def test_compute_event_hash_consistent(self):
        """Test that event hash is consistent for same inputs."""
        payload = ZohoWebhookPayload(
            account_id='account1',
            message_id='msg123',
            folder_id='INBOX',
            event_type='new_mail',
            timestamp=1234567890,
            raw_payload={}
        )
        
        hash1 = self.handler.compute_event_hash(payload)
        hash2 = self.handler.compute_event_hash(payload)
        
        assert hash1 == hash2
        assert len(hash1) == 32
    
    def test_compute_event_hash_stable_across_folder_moves(self):
        """Test that event hash is STABLE across folder moves (critical for idempotency)."""
        payload1 = ZohoWebhookPayload(
            account_id='account1',
            message_id='msg123',
            folder_id='INBOX',
            event_type='new_mail',
            timestamp=1234567890,
            raw_payload={}
        )
        
        payload2 = ZohoWebhookPayload(
            account_id='account1',
            message_id='msg123',
            folder_id='SENT',
            event_type='mail_moved',
            timestamp=1234567891,
            raw_payload={}
        )
        
        hash1 = self.handler.compute_event_hash(payload1)
        hash2 = self.handler.compute_event_hash(payload2)
        
        assert hash1 == hash2
    
    def test_validate_account_enabled(self):
        """Test account validation for enabled accounts."""
        assert self.handler.validate_account('account1') is True
        assert self.handler.validate_account('account2') is True
    
    def test_validate_account_disabled(self):
        """Test account validation for disabled/unknown accounts."""
        assert self.handler.validate_account('account3') is False
        assert self.handler.validate_account('unknown') is False
    
    def test_process_webhook_success(self):
        """Test successful webhook processing."""
        payload = {
            'account_id': 'account1',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        secret = 'secret1'
        computed_hmac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256)
        signature = base64.b64encode(computed_hmac.digest()).decode('utf-8')
        
        result = self.handler.process_webhook(payload_bytes, signature, 'account1')
        
        assert result['status'] == 'success'
        assert result['message_id'] == 'msg123'
    
    def test_process_webhook_duplicate(self):
        """Test duplicate webhook returns duplicate status."""
        payload = {
            'account_id': 'account1',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        secret = 'secret1'
        computed_hmac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256)
        signature = base64.b64encode(computed_hmac.digest()).decode('utf-8')
        
        result1 = self.handler.process_webhook(payload_bytes, signature, 'account1')
        assert result1['status'] == 'success'
        
        result2 = self.handler.process_webhook(payload_bytes, signature, 'account1')
        assert result2['status'] == 'duplicate'
        assert result2['message_id'] == 'msg123'
    
    def test_process_webhook_invalid_signature(self):
        """Test webhook with invalid signature is rejected."""
        payload = {
            'account_id': 'account1',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = "invalid_signature"
        
        result = self.handler.process_webhook(payload_bytes, signature, 'account1')
        
        assert result['status'] == 'error'
        assert result['error'] == 'invalid_signature'
    
    def test_process_webhook_sha256_prefix_rejected(self):
        """Test that sha256= prefix is rejected (Zoho doesn't use it)."""
        payload = {
            'account_id': 'account1',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        secret = 'secret1'
        computed_hmac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256)
        signature = base64.b64encode(computed_hmac.digest()).decode('utf-8')
        signature_with_prefix = f"sha256={signature}"
        
        result = self.handler.process_webhook(payload_bytes, signature_with_prefix, 'account1')
        
        assert result['status'] == 'error'
        assert result['error'] == 'invalid_signature'
    
    def test_process_webhook_oversized_payload(self):
        """Test oversized payload is rejected."""
        large_payload = {'data': 'x' * (1024 * 1024 + 1)}
        payload_bytes = json.dumps(large_payload).encode('utf-8')
        signature = "dummy"
        
        result = self.handler.process_webhook(payload_bytes, signature, 'account1')
        
        assert result['status'] == 'error'
        assert result['error'] == 'payload_too_large'
    
    def test_process_webhook_invalid_account(self):
        """Test webhook for unknown account is rejected."""
        payload = {
            'account_id': 'unknown',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = "dummy"
        
        result = self.handler.process_webhook(payload_bytes, signature, 'unknown')
        
        assert result['status'] == 'error'
        assert result['error'] == 'invalid_account'
    
    def test_process_webhook_invalid_json(self):
        """Test webhook with invalid JSON is rejected."""
        payload_bytes = b'not valid json'
        signature = "dummy"
        
        result = self.handler.process_webhook(payload_bytes, signature, 'account1')
        
        assert result['status'] == 'error'
        assert result['error'] == 'invalid_json'


class TestIntegration:
    """Integration tests simulating real Zoho webhook deliveries."""
    
    def setup_method(self):
        """Set up handler with test configuration."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.config = {
            'db_path': self.temp_db.name,
            'max_payload_size': 1024 * 1024,
            'enabled_accounts': ['account1', 'account2'],
            'secrets': {
                'account1': 'secret1',
                'account2': 'secret2'
            },
        }
        self.handler = ZohoWebhookHandler(self.config)
    
    def teardown_method(self):
        """Clean up temporary files."""
        os.unlink(self.temp_db.name)
    
    def test_zoho_like_payload_new_mail(self):
        """Test processing a realistic Zoho new mail payload."""
        payload = {
            'account_id': 'account1',
            'message_id': '189123456789012345',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': int(datetime.now().timestamp()),
            'subject': 'Test Email',
            'from': 'sender@example.com',
            'to': 'recipient@domain.com'
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        secret = 'secret1'
        computed_hmac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256)
        signature = base64.b64encode(computed_hmac.digest()).decode('utf-8')
        
        result = self.handler.process_webhook(payload_bytes, signature, 'account1')
        
        assert result['status'] == 'success'
    
    def test_folder_move_idempotency(self):
        """Test that moving mail between folders doesn't cause duplicate processing."""
        payload1 = {
            'account_id': 'account1',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        payload_bytes1 = json.dumps(payload1).encode('utf-8')
        
        secret = 'secret1'
        computed_hmac = hmac.new(secret.encode('utf-8'), payload_bytes1, hashlib.sha256)
        signature = base64.b64encode(computed_hmac.digest()).decode('utf-8')
        
        result1 = self.handler.process_webhook(payload_bytes1, signature, 'account1')
        assert result1['status'] == 'success'
        
        payload2 = {
            'account_id': 'account1',
            'message_id': 'msg123',
            'folder_id': 'PROCESSED',
            'event_type': 'mail_moved',
            'timestamp': 1234567891
        }
        payload_bytes2 = json.dumps(payload2).encode('utf-8')
        
        computed_hmac2 = hmac.new(secret.encode('utf-8'), payload_bytes2, hashlib.sha256)
        signature2 = base64.b64encode(computed_hmac2.digest()).decode('utf-8')
        
        result2 = self.handler.process_webhook(payload_bytes2, signature2, 'account1')
        assert result2['status'] == 'duplicate'
        assert result2['message_id'] == 'msg123'
    
    def test_multiple_accounts_isolation(self):
        """Test that events for different accounts are isolated."""
        payload1 = {
            'account_id': 'account1',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        payload_bytes1 = json.dumps(payload1).encode('utf-8')
        
        secret1 = 'secret1'
        computed_hmac1 = hmac.new(secret1.encode('utf-8'), payload_bytes1, hashlib.sha256)
        signature1 = base64.b64encode(computed_hmac1.digest()).decode('utf-8')
        
        result1 = self.handler.process_webhook(payload_bytes1, signature1, 'account1')
        assert result1['status'] == 'success'
        
        payload2 = {
            'account_id': 'account2',
            'message_id': 'msg123',
            'folder_id': 'INBOX',
            'event_type': 'new_mail',
            'timestamp': 1234567890
        }
        payload_bytes2 = json.dumps(payload2).encode('utf-8')
        
        secret2 = 'secret2'
        computed_hmac2 = hmac.new(secret2.encode('utf-8'), payload_bytes2, hashlib.sha256)
        signature2 = base64.b64encode(computed_hmac2.digest()).decode('utf-8')
        
        result2 = self.handler.process_webhook(payload_bytes2, signature2, 'account2')
        assert result2['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
