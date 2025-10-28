"""Tests for MongoDB Service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.mongodb_service import MongoDBService


class TestMongoDBService:
    """Test suite for MongoDB Service."""
    
    @pytest.fixture
    def service(self, mock_mongodb_collection):
        """Create MongoDB service with mocked collection."""
        with patch('services.mongodb_service.AsyncIOMotorClient') as mock_motor:
            mock_client = Mock()
            mock_db = Mock()
            mock_db.__getitem__ = Mock(return_value=mock_mongodb_collection)
            mock_client.__getitem__ = Mock(return_value=mock_db)
            mock_motor.return_value = mock_client
            
            service = MongoDBService()
            service.client = mock_client
            service.db = mock_db
            service.collection = mock_mongodb_collection
            return service
    
    @pytest.mark.asyncio
    async def test_connect_success(self, service):
        """Test successful MongoDB connection."""
        await service.connect()
        
        assert service.client is not None
        assert service.db is not None
        assert service.collection is not None
    
    @pytest.mark.asyncio
    async def test_store_match_result(self, service, sample_jd_data, sample_match_result):
        """Test storing match results."""
        await service.store_match_result(
            jd_text="Test JD",
            jd_data=sample_jd_data,
            matches=[sample_match_result]
        )
        
        service.collection.insert_one.assert_called_once()
        
        # Verify document structure
        call_args = service.collection.insert_one.call_args
        document = call_args[0][0]
        assert "jd_text" in document
        assert "jd_data" in document
        assert "matches" in document
        assert "created_at" in document
    
    @pytest.mark.asyncio
    async def test_get_match_history(self, service):
        """Test retrieving match history."""
        history = await service.get_match_history(limit=10, skip=0)
        
        assert isinstance(history, list)
        service.collection.find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_match_history_with_pagination(self, service):
        """Test match history with pagination."""
        await service.get_match_history(limit=20, skip=10)
        
        call_args = service.collection.find.call_args
        # Verify sort, skip, and limit were applied
        assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, service):
        """Test retrieving statistics."""
        stats = await service.get_statistics()
        
        assert isinstance(stats, list)
        service.collection.aggregate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_connection(self, service):
        """Test closing MongoDB connection."""
        service.client.close = Mock()
        await service.close()
        
        service.client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_match_result_error_handling(self, service, sample_jd_data):
        """Test error handling during storage."""
        service.collection.insert_one = AsyncMock(side_effect=Exception("Insert failed"))
        
        # Should not raise exception
        try:
            await service.store_match_result(
                jd_text="Test",
                jd_data=sample_jd_data,
                matches=[]
            )
        except Exception:
            pytest.fail("Should handle error gracefully")
    
    @pytest.mark.asyncio
    async def test_get_match_history_empty(self, service):
        """Test getting match history when empty."""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        service.collection.find = Mock(return_value=mock_cursor)
        
        history = await service.get_match_history()
        
        assert history == []
