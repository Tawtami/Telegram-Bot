#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for background.py
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from utils.background import BroadcastJob, BroadcastManager


class TestBroadcastJob:
    """Test cases for BroadcastJob class"""

    def test_init(self):
        """Test BroadcastJob initialization"""
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        
        assert job.job_id == "job123"
        assert job.admin_chat_id == 456
        assert job.user_ids == [1, 2, 3]
        assert job.text == "Test message"
        assert job.sent == 0
        assert job.failed == 0
        assert job.message_id is None
        assert job._task is None
        assert job._cancelled is False

    def test_set_status_message(self):
        """Test setting status message ID"""
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        
        job.set_status_message(789)
        
        assert job.message_id == 789

    def test_cancel_no_task(self):
        """Test cancel when no task exists"""
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        
        job.cancel()
        
        assert job._cancelled is True

    def test_cancel_with_task(self):
        """Test cancel with existing task"""
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        mock_task = MagicMock()
        mock_task.done.return_value = False
        job._task = mock_task
        
        job.cancel()
        
        assert job._cancelled is True
        mock_task.cancel.assert_called_once()

    def test_cancel_with_done_task(self):
        """Test cancel with already done task"""
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        mock_task = MagicMock()
        mock_task.done.return_value = True
        job._task = mock_task
        
        job.cancel()
        
        assert job._cancelled is True
        mock_task.cancel.assert_not_called()


class TestBroadcastManager:
    """Test cases for BroadcastManager class"""

    def test_init(self):
        """Test BroadcastManager initialization"""
        manager = BroadcastManager()
        
        assert manager.jobs == {}

    @pytest.mark.asyncio
    async def test_start_broadcast(self):
        """Test starting a broadcast job"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Mock the status message
        mock_status = MagicMock()
        mock_status.message_id = 123
        mock_bot.send_message.return_value = mock_status
        
        # Mock the background task
        mock_task = MagicMock()
        
        with patch('asyncio.create_task', return_value=mock_task) as mock_create_task:
            job_id = await manager.start_broadcast(mock_app, 456, [1, 2, 3], "Test message")
        
        # Verify job was created
        assert job_id in manager.jobs
        job = manager.jobs[job_id]
        assert job.admin_chat_id == 456
        assert job.user_ids == [1, 2, 3]
        assert job.text == "Test message"
        assert job.message_id == 123
        
        # Verify initial status message was sent
        mock_bot.send_message.assert_called_once_with(
            chat_id=456,
            text="🚀 شروع ارسال برای 3 کاربر... 0%"
        )
        
        # Verify background task was created
        mock_create_task.assert_called_once()
        assert job._task == mock_task

    @pytest.mark.asyncio
    async def test_run_broadcast_success(self):
        """Test successful broadcast execution"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Create a job
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        job.message_id = 123
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify all messages were sent
        assert mock_bot.send_message.call_count == 3
        mock_bot.send_message.assert_any_call(chat_id=1, text="Test message")
        mock_bot.send_message.assert_any_call(chat_id=2, text="Test message")
        mock_bot.send_message.assert_any_call(chat_id=3, text="Test message")
        
        # Verify final status
        assert job.sent == 3
        assert job.failed == 0

    @pytest.mark.asyncio
    async def test_run_broadcast_with_failures(self):
        """Test broadcast execution with some failures"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Make second message fail
        mock_bot.send_message.side_effect = [
            None,  # First message succeeds
            Exception("Network error"),  # Second message fails
            None   # Third message succeeds
        ]
        
        # Create a job
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        job.message_id = 123
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify final status
        assert job.sent == 2
        assert job.failed == 1

    @pytest.mark.asyncio
    async def test_run_broadcast_all_failures(self):
        """Test broadcast execution with all failures"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Make all messages fail
        mock_bot.send_message.side_effect = Exception("Network error")
        
        # Create a job
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        job.message_id = 123
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify final status
        assert job.sent == 0
        assert job.failed == 3

    @pytest.mark.asyncio
    async def test_run_broadcast_cancelled(self):
        """Test broadcast execution when cancelled"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Create a job
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        job.message_id = 123
        
        # Mock the background task execution and cancel it
        with patch('asyncio.create_task') as mock_create_task:
            # Simulate cancellation by making the task raise CancelledError
            mock_bot.send_message.side_effect = asyncio.CancelledError()
            
            await manager._run_broadcast(mock_app, job)
        
        # Verify job was cancelled
        assert job.sent == 0
        assert job.failed == 0

    @pytest.mark.asyncio
    async def test_run_broadcast_progress_updates(self):
        """Test that progress updates are sent during broadcast"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Create a job with many users to trigger progress updates
        user_ids = list(range(1, 21))  # 20 users
        job = BroadcastJob("job123", 456, user_ids, "Test message")
        job.message_id = 123
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify progress updates were sent (should be called multiple times)
        assert mock_bot.edit_message_text.call_count > 0
        
        # Verify final status message
        mock_bot.edit_message_text.assert_any_call(
            chat_id=456,
            message_id=123,
            text="✅ پایان ارسال | موفق: 20 | ناموفق: 0"
        )

    @pytest.mark.asyncio
    async def test_run_broadcast_empty_user_list(self):
        """Test broadcast execution with empty user list"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Create a job with no users
        job = BroadcastJob("job123", 456, [], "Test message")
        job.message_id = 123
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify no messages were sent
        mock_bot.send_message.assert_not_called()
        
        # Verify final status
        assert job.sent == 0
        assert job.failed == 0

    @pytest.mark.asyncio
    async def test_run_broadcast_single_user(self):
        """Test broadcast execution with single user"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Create a job with single user
        job = BroadcastJob("job123", 456, [1], "Test message")
        job.message_id = 123
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify message was sent
        mock_bot.send_message.assert_called_once_with(chat_id=1, text="Test message")
        
        # Verify final status
        assert job.sent == 1
        assert job.failed == 0

    @pytest.mark.asyncio
    async def test_run_broadcast_message_edit_failures(self):
        """Test broadcast execution when message editing fails"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Make message editing fail
        mock_bot.edit_message_text.side_effect = Exception("Edit failed")
        
        # Create a job
        job = BroadcastJob("job123", 456, [1, 2, 3], "Test message")
        job.message_id = 123
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify messages were still sent despite edit failures
        assert mock_bot.send_message.call_count == 3
        assert job.sent == 3
        assert job.failed == 0

    @pytest.mark.asyncio
    async def test_run_broadcast_final_status_edit_failure(self):
        """Test broadcast execution when final status edit fails"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Make final status edit fail
        mock_bot.edit_message_text.side_effect = [
            None,  # Progress updates succeed
            Exception("Final edit failed")  # Final status fails
        ]
        
        # Create a job
        job = BroadcastJob("job123", 456, [1], "Test message")
        job.message_id = 123
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify message was sent despite final edit failure
        mock_bot.send_message.assert_called_once_with(chat_id=1, text="Test message")
        assert job.sent == 1
        assert job.failed == 0

    @pytest.mark.asyncio
    async def test_run_broadcast_concurrency_limit(self):
        """Test that broadcast respects concurrency limit"""
        manager = BroadcastManager()
        mock_app = MagicMock()
        mock_bot = AsyncMock()
        mock_app.bot = mock_bot
        
        # Create a job with many users
        user_ids = list(range(1, 21))  # 20 users
        job = BroadcastJob("job123", 456, user_ids, "Test message")
        job.message_id = 123
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        
        async def track_concurrency():
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)  # Small delay to allow concurrency
            concurrent_count -= 1
        
        # Mock send_message to track concurrency
        mock_bot.send_message.side_effect = track_concurrency
        
        # Mock the background task execution
        with patch('asyncio.create_task') as mock_create_task:
            await manager._run_broadcast(mock_app, job)
        
        # Verify concurrency was limited (should be around 8 due to semaphore)
        assert max_concurrent <= 8
        assert job.sent == 20
        assert job.failed == 0
