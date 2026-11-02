import unittest
from unittest.mock import AsyncMock
from askai.core.permissions.grants import GrantPolicy


class AsyncGrantsTests(unittest.IsolatedAsyncioTestCase):
    async def test_async_confirmation_carries_same_scope_as_sync(self):
        policy = GrantPolicy(lambda key: 'ask')
        confirm = AsyncMock(return_value=True)
        self.assertTrue(await policy.authorize_async(['media.play.local'], 'Play?', confirm))
        confirm.assert_awaited_once_with('Play?', grants=['askai.grants.media.play.local'])
