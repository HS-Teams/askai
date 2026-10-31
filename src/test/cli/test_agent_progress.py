import unittest
from unittest.mock import Mock, patch
from askai.cli.agent_progress import AgentProgress
from askai.core.agents.contracts import AgentEvent


class ProgressTests(unittest.TestCase):
    def setUp(self):
        patcher = patch('askai.cli.agent_progress.Status')
        self.status = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.interaction = Mock(return_value={'decision': 'accept'})
        self.progress = AgentProgress(Mock(), self.interaction)

    def test_updates_one_spinner_and_clears_at_end(self):
        self.progress.emit(AgentEvent('stage', '', data={'stage': 'retrieval'}))
        self.progress.emit(AgentEvent('progress', 's', data={'type': 'commandExecution'}))
        self.status.update.assert_called_with('Executando comando…')
        self.progress.emit(AgentEvent('completed', 's'))
        self.status.stop.assert_not_called()
        self.progress.emit(AgentEvent('stage', 's', data={'stage': 'validation'}))
        self.status.update.assert_called_with('Validando resposta…')
        self.status.start.assert_called_once()
        self.progress.emit(AgentEvent('finished', ''))
        self.status.stop.assert_called_once()

    def test_approval_pauses_and_resumes_spinner(self):
        self.progress.emit(AgentEvent('stage', '', data={'stage': 'execution'}))
        self.assertEqual(self.progress.interact('approval', {}), {'decision': 'accept'})
        self.status.stop.assert_called_once()
        self.assertEqual(self.status.start.call_count, 2)
        self.interaction.assert_called_once_with('approval', {})

    def test_compaction_uses_translated_progress(self):
        with patch('askai.core.askai_messages.msg.translate', return_value='Compacting translated') as translate:
            self.progress.emit(AgentEvent('stage', 's', data={'stage': 'compaction'}))
        translate.assert_called_once_with('Compactando histórico…')
        self.status.update.assert_called_with('Compacting translated')

    def test_camera_leaves_terminal_free_for_original_countdown(self):
        self.progress.emit(AgentEvent('stage', 's', data={'stage': 'execution'}))
        self.progress.emit(AgentEvent('camera_started', 's'))
        self.status.stop.assert_called_once()
        self.progress.emit(AgentEvent('camera_finished', 's'))
        self.assertEqual(self.status.start.call_count, 2)
