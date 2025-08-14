#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for admin_notify.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from utils.admin_notify import notify_admins, send_paginated_list


class TestNotifyAdmins:
    """Test cases for notify_admins function"""

    @pytest.mark.asyncio
    async def test_notify_admins_success(self):
        """Test successful notification to all admins"""
        mock_context = MagicMock()
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        admin_ids = [123, 456, 789]
        text = "Test notification"
        
        await notify_admins(mock_context, admin_ids, text)
        
        assert mock_bot.send_message.call_count == 3
        mock_bot.send_message.assert_any_call(chat_id=123, text=text, parse_mode=None)
        mock_bot.send_message.assert_any_call(chat_id=456, text=text, parse_mode=None)
        mock_bot.send_message.assert_any_call(chat_id=789, text=text, parse_mode=None)

    @pytest.mark.asyncio
    async def test_notify_admins_with_parse_mode(self):
        """Test notification with parse_mode"""
        mock_context = MagicMock()
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        admin_ids = [123]
        text = "Test notification"
        parse_mode = "HTML"
        
        await notify_admins(mock_context, admin_ids, text, parse_mode)
        
        mock_bot.send_message.assert_called_once_with(
            chat_id=123, text=text, parse_mode=parse_mode
        )

    @pytest.mark.asyncio
    async def test_notify_admins_empty_list(self):
        """Test notification with empty admin list"""
        mock_context = MagicMock()
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        admin_ids = []
        text = "Test notification"
        
        await notify_admins(mock_context, admin_ids, text)
        
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_admins_none_list(self):
        """Test notification with None admin list"""
        mock_context = MagicMock()
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        admin_ids = None
        text = "Test notification"
        
        await notify_admins(mock_context, admin_ids, text)
        
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_admins_partial_failure(self):
        """Test notification when some admins fail but others succeed"""
        mock_context = MagicMock()
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        # First call succeeds, second fails, third succeeds
        mock_bot.send_message.side_effect = [
            None,  # Success for first admin
            Exception("Connection error"),  # Failure for second admin
            None   # Success for third admin
        ]
        
        admin_ids = [123, 456, 789]
        text = "Test notification"
        
        await notify_admins(mock_context, admin_ids, text)
        
        # Should still attempt all 3 calls despite one failure
        assert mock_bot.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_notify_admins_all_failures(self):
        """Test notification when all admins fail"""
        mock_context = MagicMock()
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        # All calls fail
        mock_bot.send_message.side_effect = Exception("Network error")
        
        admin_ids = [123, 456, 789]
        text = "Test notification"
        
        # Should not raise exception, should continue through all admins
        await notify_admins(mock_context, admin_ids, text)
        
        assert mock_bot.send_message.call_count == 3


class TestSendPaginatedList:
    """Test cases for send_paginated_list function"""

    @pytest.mark.asyncio
    async def test_send_paginated_list_empty_lines(self):
        """Test pagination with empty lines list"""
        mock_context = MagicMock()
        admin_ids = [123]
        title = "Test Title"
        lines = []
        
        with patch('utils.admin_notify.notify_admins') as mock_notify:
            await send_paginated_list(mock_context, admin_ids, title, lines)
            
            mock_notify.assert_called_once_with(
                mock_context, admin_ids, "Test Title\n— خالی —"
            )

    @pytest.mark.asyncio
    async def test_send_paginated_list_single_page(self):
        """Test pagination with lines fitting in single page"""
        mock_context = MagicMock()
        admin_ids = [123]
        title = "Test Title"
        lines = ["Line 1", "Line 2", "Line 3"]
        page_size = 50
        
        with patch('utils.admin_notify.notify_admins') as mock_notify:
            await send_paginated_list(mock_context, admin_ids, title, lines, page_size)
            
            mock_notify.assert_called_once_with(
                mock_context, admin_ids, "Test Title\nLine 1\nLine 2\nLine 3"
            )

    @pytest.mark.asyncio
    async def test_send_paginated_list_exact_page_size(self):
        """Test pagination with lines exactly matching page size"""
        mock_context = MagicMock()
        admin_ids = [123]
        title = "Test Title"
        lines = ["Line 1", "Line 2"]
        page_size = 2
        
        with patch('utils.admin_notify.notify_admins') as mock_notify:
            await send_paginated_list(mock_context, admin_ids, title, lines, page_size)
            
            mock_notify.assert_called_once_with(
                mock_context, admin_ids, "Test Title\nLine 1\nLine 2"
            )

    @pytest.mark.asyncio
    async def test_send_paginated_list_multiple_pages(self):
        """Test pagination with multiple pages"""
        mock_context = MagicMock()
        admin_ids = [123]
        title = "Test Title"
        lines = ["Line 1", "Line 2", "Line 3", "Line 4"]
        page_size = 2
        
        with patch('utils.admin_notify.notify_admins') as mock_notify:
            await send_paginated_list(mock_context, admin_ids, title, lines, page_size)
            
            # Should be called 2 times: 2 lines per page, 4 total lines
            assert mock_notify.call_count == 2
            
            # First page
            mock_notify.assert_any_call(
                mock_context, admin_ids, "Test Title\nLine 1\nLine 2"
            )
            # Second page
            mock_notify.assert_any_call(
                mock_context, admin_ids, "Test Title\nLine 3\nLine 4"
            )

    @pytest.mark.asyncio
    async def test_send_paginated_list_remainder_page(self):
        """Test pagination with remainder lines in last page"""
        mock_context = MagicMock()
        admin_ids = [123]
        title = "Test Title"
        lines = ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]
        page_size = 2
        
        with patch('utils.admin_notify.notify_admins') as mock_notify:
            await send_paginated_list(mock_context, admin_ids, title, lines, page_size)
            
            # Should be called 3 times: 2 full pages + 1 remainder page
            assert mock_notify.call_count == 3
            
            # First page
            mock_notify.assert_any_call(
                mock_context, admin_ids, "Test Title\nLine 1\nLine 2"
            )
            # Second page
            mock_notify.assert_any_call(
                mock_context, admin_ids, "Test Title\nLine 3\nLine 4"
            )
            # Third page (remainder)
            mock_notify.assert_any_call(
                mock_context, admin_ids, "Test Title\nLine 5"
            )

    @pytest.mark.asyncio
    async def test_send_paginated_list_default_page_size(self):
        """Test pagination with default page size"""
        mock_context = MagicMock()
        admin_ids = [123]
        title = "Test Title"
        lines = ["Line 1", "Line 2", "Line 3"]
        
        with patch('utils.admin_notify.notify_admins') as mock_notify:
            await send_paginated_list(mock_context, admin_ids, title, lines)
            
            # Should use default page_size of 50, so all lines fit in one page
            mock_notify.assert_called_once_with(
                mock_context, admin_ids, "Test Title\nLine 1\nLine 2\nLine 3"
            )

    @pytest.mark.asyncio
    async def test_send_paginated_list_large_dataset(self):
        """Test pagination with large dataset"""
        mock_context = MagicMock()
        admin_ids = [123]
        title = "Test Title"
        lines = [f"Line {i}" for i in range(1, 101)]  # 100 lines
        page_size = 25
        
        with patch('utils.admin_notify.notify_admins') as mock_notify:
            await send_paginated_list(mock_context, admin_ids, title, lines, page_size)
            
            # Should be called 4 times: 100 lines / 25 per page = 4 pages
            assert mock_notify.call_count == 4
            
            # Verify first page
            mock_notify.assert_any_call(
                mock_context, admin_ids, 
                "Test Title\n" + "\n".join([f"Line {i}" for i in range(1, 26)])
            )
            
            # Verify last page
            mock_notify.assert_any_call(
                mock_context, admin_ids, 
                "Test Title\n" + "\n".join([f"Line {i}" for i in range(76, 101)])
            )
