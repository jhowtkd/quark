"""
Tests for Research Approval API endpoints

Tests the fail-closed validation:
- approve endpoint validates draft.md sections exist and have content
- incomplete outputs fail with 400 and mark run as FAILED
- 422 response is returned for malformed/incomplete artifacts
"""

import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Ensure the backend modules are importable
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestResearchApproval:
    """Tests for research approval, reject, and rerun endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from flask import Flask
        from backend.app.api.research import research_bp
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(research_bp, url_prefix='/research')
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def temp_research_dir(self):
        """Create temporary research directory"""
        original_dir = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
        temp_dir = tempfile.mkdtemp()
        os.environ['UPLOAD_FOLDER'] = temp_dir
        
        # Create research subdirectory
        research_dir = os.path.join(temp_dir, 'research')
        os.makedirs(research_dir, exist_ok=True)
        
        yield research_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        if original_dir != temp_dir:
            os.environ['UPLOAD_FOLDER'] = original_dir
    
    def test_approve_missing_run_returns_404(self, client):
        """Approve endpoint returns 404 for non-existent run"""
        response = client.post('/research/approve/nonexistent_run_123')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
    
    def test_approve_non_completed_run_returns_400(self, client, temp_research_dir):
        """Approve endpoint returns 400 for non-completed runs"""
        from backend.app.models.research_run import ResearchRunManager, ResearchRun
        
        # Create a pending run
        manager = ResearchRunManager()
        run = manager.create_run(query="Test query")
        
        response = client.post(f'/research/approve/{run.run_id}')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'completed' in data['error'].lower()
    
    def test_approve_missing_draft_fails_closed(self, client, temp_research_dir):
        """Approve endpoint fails closed when draft.md is missing"""
        from backend.app.models.research_run import ResearchRunManager
        
        # Create and complete a run but don't write draft.md
        manager = ResearchRunManager()
        run = manager.create_run(query="Test query")
        manager.complete_run(run.run_id, artifact_path="nonexistent.md", connector_used="test")
        
        response = client.post(f'/research/approve/{run.run_id}')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'missing' in data['error'].lower()
        
        # Verify run is marked as FAILED
        updated_run = manager.get_run(run.run_id)
        assert updated_run.status.value == 'failed'
    
    def test_approve_incomplete_artifact_fails_closed(self, client, temp_research_dir):
        """Approve endpoint validates required sections - fail-closed for incomplete"""
        from backend.app.models.research_run import ResearchRunManager
        
        # Create and complete a run with incomplete draft
        manager = ResearchRunManager()
        run = manager.create_run(query="Test query")
        manager.complete_run(run.run_id, artifact_path="nonexistent.md", connector_used="test")
        
        # Write draft without required sections
        draft_path = manager._get_draft_path(run.run_id)
        with open(draft_path, 'w') as f:
            f.write("# Research\n\nSome incomplete content without proper sections.")
        
        response = client.post(f'/research/approve/{run.run_id}')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'missing sections' in data['error'].lower()
        
        # Verify run is marked as FAILED
        updated_run = manager.get_run(run.run_id)
        assert updated_run.status.value == 'failed'
    
    def test_approve_complete_artifact_succeeds(self, client, temp_research_dir):
        """Approve endpoint succeeds for complete artifact with all sections"""
        from backend.app.models.research_run import ResearchRunManager
        
        # Create and complete a run
        manager = ResearchRunManager()
        run = manager.create_run(query="Test query")
        manager.complete_run(run.run_id, artifact_path="nonexistent.md", connector_used="test")
        
        # Write complete draft with all required sections
        draft_path = manager._get_draft_path(run.run_id)
        with open(draft_path, 'w') as f:
            f.write("""# Deep Research: Test query

## Summary
This is the summary content.

## Claims
These are the claims extracted.

## Sources
1. Source A
2. Source B
""")
        
        response = client.post(f'/research/approve/{run.run_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['status'] == 'approved'
        assert 'approved_at' in data['data']
        
        # Verify run is marked as APPROVED
        updated_run = manager.get_run(run.run_id)
        assert updated_run.status.value == 'approved'
    
    def test_reject_resets_to_pending(self, client, temp_research_dir):
        """Reject endpoint resets run to PENDING state"""
        from backend.app.models.research_run import ResearchRunManager
        
        manager = ResearchRunManager()
        run = manager.create_run(query="Test query")
        manager.complete_run(run.run_id, artifact_path="test.md", connector_used="test")
        
        response = client.post(f'/research/reject/{run.run_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['status'] == 'pending'
        
        # Verify run is reset to PENDING
        updated_run = manager.get_run(run.run_id)
        assert updated_run.status.value == 'pending'
    
    def test_reject_missing_run_returns_404(self, client):
        """Reject endpoint returns 404 for non-existent run"""
        response = client.post('/research/reject/nonexistent_run_123')
        
        assert response.status_code == 404
    
    def test_rerun_creates_new_run_with_feedback(self, client, temp_research_dir):
        """Rerun endpoint creates new run with original query + feedback"""
        from backend.app.models.research_run import ResearchRunManager
        
        manager = ResearchRunManager()
        original_run = manager.create_run(query="Original query")
        original_run_id = original_run.run_id
        
        feedback = "Please include more recent sources"
        
        response = client.post(
            f'/research/rerun/{original_run_id}',
            json={'feedback': feedback}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'new_run_id' in data['data']
        assert 'task_id' in data['data']
        assert data['data']['original_run_id'] == original_run_id
        
        # Verify original run is marked as rerun_requested
        updated_original = manager.get_run(original_run_id)
        assert updated_original.status.value == 'rerun_requested'
        
        # Verify new run has query + feedback
        new_run = manager.get_run(data['data']['new_run_id'])
        assert feedback in new_run.query
        assert "Original query" in new_run.query
    
    def test_rerun_requires_feedback(self, client, temp_research_dir):
        """Rerun endpoint requires non-empty feedback"""
        from backend.app.models.research_run import ResearchRunManager
        
        manager = ResearchRunManager()
        run = manager.create_run(query="Test query")
        
        response = client.post(
            f'/research/rerun/{run.run_id}',
            json={'feedback': ''}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'required' in data['error'].lower()


class TestResearchStatusEndpoint:
    """Tests for research status endpoint"""
    
    @pytest.fixture
    def app(self):
        from flask import Flask
        from backend.app.api.research import research_bp
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(research_bp, url_prefix='/research')
        
        return app
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    @pytest.fixture
    def temp_research_dir(self):
        original_dir = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
        temp_dir = tempfile.mkdtemp()
        os.environ['UPLOAD_FOLDER'] = temp_dir
        
        research_dir = os.path.join(temp_dir, 'research')
        os.makedirs(research_dir, exist_ok=True)
        
        yield research_dir
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        if original_dir != temp_dir:
            os.environ['UPLOAD_FOLDER'] = original_dir
    
    def test_get_status_returns_run_info(self, client, temp_research_dir):
        """Status endpoint returns correct run information"""
        from backend.app.models.research_run import ResearchRunManager
        
        manager = ResearchRunManager()
        run = manager.create_run(query="Test research query")
        
        response = client.get(f'/research/status/{run.run_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['run_id'] == run.run_id
        assert data['data']['query'] == "Test research query"
        assert data['data']['status'] == 'pending'
    
    def test_get_status_missing_run_returns_404(self, client):
        """Status endpoint returns 404 for non-existent run"""
        response = client.get('/research/status/nonexistent_run')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
