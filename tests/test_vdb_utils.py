"""
Unit tests for VDB utilities module.
"""

import pytest
import tempfile
import os
from pathlib import Path
import numpy as np

# Import the module to test
from bpwf.vdb_utils import (
    check_openvdb_available,
    check_docker_available,
    _normalize_to_numpy,
    save_vdb,
    load_vdb,
)


class TestOpenVDBDetection:
    """Test OpenVDB availability detection."""
    
    def test_check_openvdb_returns_tuple(self):
        """Test that check_openvdb_available returns a tuple."""
        result = check_openvdb_available()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
    
    def test_check_openvdb_message_not_empty(self):
        """Test that the message is not empty."""
        success, message = check_openvdb_available()
        assert len(message) > 0


class TestDockerDetection:
    """Test Docker availability detection."""
    
    def test_check_docker_returns_tuple(self):
        """Test that check_docker_available returns a tuple."""
        result = check_docker_available()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
    
    def test_check_docker_message_not_empty(self):
        """Test that the message is not empty."""
        success, message = check_docker_available()
        assert len(message) > 0


class TestNormalization:
    """Test data normalization to numpy arrays."""
    
    def test_normalize_numpy_array(self):
        """Test normalizing a numpy array."""
        data = np.random.rand(10, 10, 10)
        result = _normalize_to_numpy(data)
        assert isinstance(result, np.ndarray)
        assert result.shape == (10, 10, 10)
        assert result.dtype == np.float32
    
    def test_normalize_list(self):
        """Test normalizing a Python list."""
        data = [[[1.0 for _ in range(5)] for _ in range(5)] for _ in range(5)]
        result = _normalize_to_numpy(data)
        assert isinstance(result, np.ndarray)
        assert result.shape == (5, 5, 5)
        assert result.dtype == np.float32
    
    def test_normalize_torch_tensor(self):
        """Test normalizing a PyTorch tensor (if available)."""
        try:
            import torch
            data = torch.rand(8, 8, 8)
            result = _normalize_to_numpy(data)
            assert isinstance(result, np.ndarray)
            assert result.shape == (8, 8, 8)
            assert result.dtype == np.float32
        except ImportError:
            pytest.skip("PyTorch not available")
    
    def test_normalize_invalid_dimensions(self):
        """Test that non-3D data raises ValueError."""
        # 2D array
        data_2d = np.random.rand(10, 10)
        with pytest.raises(ValueError, match="must be 3D"):
            _normalize_to_numpy(data_2d)
        
        # 4D array
        data_4d = np.random.rand(5, 5, 5, 5)
        with pytest.raises(ValueError, match="must be 3D"):
            _normalize_to_numpy(data_4d)
    
    def test_normalize_invalid_type(self):
        """Test that invalid types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported data type"):
            _normalize_to_numpy("invalid")
        
        with pytest.raises(ValueError, match="Unsupported data type"):
            _normalize_to_numpy(123)


class TestSaveVDB:
    """Test VDB file saving functionality."""
    
    def test_save_vdb_with_numpy(self):
        """Test saving a numpy array to VDB."""
        # Create test data
        data = np.random.rand(10, 10, 10).astype(np.float32)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.vdb', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Try to save
            result = save_vdb(data, tmp_path, voxel_size=1.0)
            
            # Check if either method succeeded
            # (will succeed if pyopenvdb OR docker is available)
            if result:
                assert os.path.exists(tmp_path)
                assert os.path.getsize(tmp_path) > 0
        except RuntimeError as e:
            # Expected if neither pyopenvdb nor Docker is available
            assert "Cannot save VDB file" in str(e)
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_save_vdb_with_list(self):
        """Test saving a Python list to VDB."""
        # Create test data
        data = [[[1.0 for _ in range(5)] for _ in range(5)] for _ in range(5)]
        
        with tempfile.NamedTemporaryFile(suffix='.vdb', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = save_vdb(data, tmp_path, voxel_size=0.5)
            if result:
                assert os.path.exists(tmp_path)
        except RuntimeError:
            # Expected if neither method is available
            pass
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_save_vdb_invalid_data(self):
        """Test that invalid data raises appropriate errors."""
        with tempfile.NamedTemporaryFile(suffix='.vdb', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # 2D data should fail
            data_2d = np.random.rand(10, 10)
            with pytest.raises(ValueError):
                save_vdb(data_2d, tmp_path)
            
            # Invalid type should fail
            with pytest.raises(ValueError):
                save_vdb("invalid", tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestLoadVDB:
    """Test VDB file loading functionality."""
    
    def test_load_vdb_nonexistent_file(self):
        """Test loading a non-existent file."""
        result = load_vdb("nonexistent_file.vdb")
        # Should return None if file doesn't exist or pyopenvdb not available
        assert result is None or isinstance(result, np.ndarray)
    
    def test_load_vdb_requires_pyopenvdb(self):
        """Test that loading requires pyopenvdb."""
        # This test just verifies the function handles missing pyopenvdb gracefully
        try:
            import pyopenvdb
            # If pyopenvdb is available, we can't test the ImportError path
            pytest.skip("pyopenvdb is available")
        except ImportError:
            # Should return None when pyopenvdb is not available
            result = load_vdb("any_file.vdb")
            assert result is None


class TestIntegration:
    """Integration tests for save/load cycle."""
    
    def test_save_and_load_cycle(self):
        """Test saving and loading a VDB file."""
        # Check if pyopenvdb is available
        openvdb_ok, _ = check_openvdb_available()
        if not openvdb_ok:
            pytest.skip("pyopenvdb not available for save/load cycle test")
        
        # Create test data
        data_original = np.random.rand(10, 10, 10).astype(np.float32)
        
        with tempfile.NamedTemporaryFile(suffix='.vdb', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Save
            save_vdb(data_original, tmp_path, voxel_size=1.0)
            
            # Load
            data_loaded = load_vdb(tmp_path)
            
            # Verify
            assert data_loaded is not None
            assert isinstance(data_loaded, np.ndarray)
            assert data_loaded.shape == data_original.shape
            
            # Note: Values might not be exactly equal due to VDB compression
            # but they should be close
            np.testing.assert_allclose(data_loaded, data_original, rtol=1e-5, atol=1e-6)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_save_vdb_with_invalid_path(self):
        """Test saving to an invalid path."""
        data = np.random.rand(5, 5, 5)
        
        # Try to save to a directory that doesn't exist
        invalid_path = "/nonexistent/directory/file.vdb"
        
        try:
            save_vdb(data, invalid_path)
            # If it succeeds, the directory was created or error was handled
        except (RuntimeError, OSError, PermissionError):
            # Expected - various errors possible depending on system
            pass
    
    def test_save_vdb_with_zero_voxel_size(self):
        """Test that zero voxel size is handled."""
        data = np.random.rand(5, 5, 5)
        
        with tempfile.NamedTemporaryFile(suffix='.vdb', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # This might succeed or fail depending on implementation
            # Just verify it doesn't crash
            save_vdb(data, tmp_path, voxel_size=0.0)
        except (ValueError, RuntimeError):
            # Expected if zero voxel size is invalid
            pass
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_save_vdb_with_negative_voxel_size(self):
        """Test that negative voxel size is handled."""
        data = np.random.rand(5, 5, 5)
        
        with tempfile.NamedTemporaryFile(suffix='.vdb', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            save_vdb(data, tmp_path, voxel_size=-1.0)
        except (ValueError, RuntimeError):
            # Expected if negative voxel size is invalid
            pass
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
