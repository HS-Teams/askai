"""Present quota snapshots independently of the conversation pipeline."""
from askai.core.support.usage import engine_usage, read_usage, reset_time


class UsageCmd:
    @staticmethod
    def show():
        from askai.core.askai_messages import msg
        from askai.core.askai_configs import configs
        from askai.core.support.shared_instances import shared
        from askai.cli import output as cli_output
        from rich.table import Table

        rows = engine_usage(configs.agent, shared.engine)
        rows += read_usage(configs.tts_engine, shared.speech.tts.usage)
        translator = msg.translator
        rows += read_usage(translator.name(), translator.usage)
        table = Table(title=msg.t('Remaining usage'))
        for heading in ('Provider', 'Remaining', 'Window / unit', 'Resets at'):
            table.add_column(msg.t(heading), style='cyan' if heading == 'Provider' else None)
        for row in rows:
            if row.error:
                table.add_row(row.provider, msg.t('Unavailable'), msg.t(row.error), '-')
            else:
                table.add_row(row.provider, row.remaining, msg.t(row.window), reset_time(row.resets_at))
        cli_output.console.print(table)
