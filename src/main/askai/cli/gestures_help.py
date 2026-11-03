"""Detailed gesture help using the same timing and angle constants as detection."""
from io import StringIO
from rich import box
from rich.console import Console
from rich.table import Table
from askai.cli.help_formatter import HelpCommand


def gesture_tables(width=80):
    from askai.gestures.command import MESSAGES
    from askai.gestures.controller import GestureController as Control
    from askai.gestures.session import INACTIVITY_SECONDS, RESUME_HOLD_SECONDS, PAUSE_WARNING_SECONDS, PAUSE_STOP_SECONDS
    from askai.gestures.scroll import SCROLL_INTERVAL, MAX_STEPS, TOP_LIMIT, BOTTOM_LIMIT, NEUTRAL_TOP, NEUTRAL_BOTTOM

    def seconds(value):
        return f'{value:g}'.replace('.', ',') + ' s'

    pinch_cooldown = seconds(Control.PINCH_COOLDOWN_SECONDS) + ' após soltar; abrir antes de repetir'
    rows = [
        ('Indicador apontando', 'Mover ponteiro', 'Imediato', 'Contínuo'),
        ('Fechar e abrir pinça', 'Clique simples', 'Imediato', pinch_cooldown),
        ('Manter pinça e mover', 'Arrastar', seconds(Control.DRAG_HOLD_SECONDS), pinch_cooldown),
        ('Mão espalmada', 'Duplo clique', seconds(Control.DOUBLE_CLICK_HOLD_SECONDS),
         seconds(Control.DOUBLE_CLICK_COOLDOWN_SECONDS) + ' após disparar; desfazer e repetir'),
        ('Heavy Metal', 'Abort da operação do AskAI', seconds(Control.ABORT_HOLD_SECONDS),
         seconds(Control.ABORT_COOLDOWN_SECONDS) + ' após disparar; desfazer e repetir'),
        ('Telefone', 'Entrada por voz', seconds(Control.EXIT_HOLD_SECONDS), 'Sem cooldown; desfazer e repetir'),
        ('PTT ou ditado ativo', 'Pausar controle', 'Ao iniciar', 'Após terminar, mão válida por '
         + seconds(RESUME_HOLD_SECONDS) + ' para retomar'),
        ('Joinha', 'Encerrar controle', seconds(Control.EXIT_HOLD_SECONDS), 'Encerra a sessão'),
        ('Dois dedos', 'Rolar pela altura da mão', 'Imediato', 'Enquanto mantiver os dois dedos'),
        ('Após desfazer os dois dedos', 'Retomar todos os gestos', seconds(Control.SCROLL_COOLDOWN_SECONDS), 'Todos os gestos bloqueados na espera'),
        ('Mão ausente ou inválida na área permitida', 'Pausar controle', seconds(INACTIVITY_SECONDS), 'Aguarda retomada'),
        ('Mão válida reaparece acima do quadril', 'Retomar controle', seconds(RESUME_HOLD_SECONDS) + ' contínuos',
         'Perder a detecção reinicia a espera'),
        ('Quadril não detectado', 'Pausar controle', seconds(INACTIVITY_SECONDS), 'Aviso para ajustar o corpo'),
        ('Controle em pausa', 'Aviso de desativação', seconds(PAUSE_WARNING_SECONDS), 'Uma vez por pausa'),
        ('Controle em pausa', 'Encerrar, como /gestures stop', seconds(PAUSE_STOP_SECONDS), 'Fecha câmera e detector'),
    ]
    output = StringIO()
    console = Console(file=output, width=width, force_terminal=False, color_system=None)
    table = Table(title='Gestos, ativação e cooldowns', box=box.SIMPLE, show_lines=True)
    for heading, ratio in (('Gesto / condição', 2), ('Ação', 2), ('Ativação', 1), ('Cooldown / repetição', 3)):
        table.add_column(heading, ratio=ratio)
    for row in rows:
        table.add_row(*row)
    console.print(table)
    console.print('Mão direita; polegar e indicador acima da linha do quadril detectado.', markup=False)
    console.print(f'O rodapé da tela é alcançado a {(1 - Control.CAMERA_MARGIN):.0%} da altura até o quadril; '
                  f'os {Control.CAMERA_MARGIN:.0%} restantes dão margem para fechar a pinça.', markup=False)
    console.print('Sem quadril confiável, comandos são bloqueados imediatamente; a pausa começa após '
                  + seconds(INACTIVITY_SECONDS) + '.', markup=False)
    console.print('Inatividade = tempo em pausa por mão ou quadril inválidos. Retomar zera a contagem.', markup=False)
    console.print('Durante o PTT ou ditado, a pausa não conta como inatividade e não fecha câmera ou detector.', markup=False)
    console.print('Aviso de sistema: ' + MESSAGES['inactivity_warning'], markup=False)
    directions = Table(title='Rolagem pela altura da mão na imagem da câmera', box=box.SIMPLE)
    for heading in ('Posição do punho (a partir do topo)', 'Direção', 'Avanço'):
        directions.add_column(heading)
    rate = f'1 a {MAX_STEPS} passos a cada {seconds(SCROLL_INTERVAL)}'
    for row in ((f'Até {TOP_LIMIT:.0%}', 'Início do conteúdo', 'Ao entrar no limite'),
                (f'Entre {TOP_LIMIT:.0%} e {NEUTRAL_TOP:.0%}', 'Para cima', rate),
                (f'De {NEUTRAL_TOP:.0%} a {NEUTRAL_BOTTOM:.0%}', 'Parada', 'Faixa neutra'),
                (f'Entre {NEUTRAL_BOTTOM:.0%} e {BOTTOM_LIMIT:.0%}', 'Para baixo', rate),
                (f'A partir de {BOTTOM_LIMIT:.0%}', 'Fim do conteúdo', 'Ao entrar no limite')):
        directions.add_row(*row)
    console.print(directions)
    console.print('Durante a rolagem, o ponteiro fica parado, inclusive na faixa neutra.', markup=False)
    console.print('Mantenha os dois dedos para rolar; a altura do punho define a direção e a velocidade. '
                  'Quanto mais longe do centro, mais rápida a rolagem.', markup=False)
    console.print('Indicador e médio estendidos, juntos ou afastados; anelar e mínimo dobrados. '
                  'O polegar pode ficar recolhido ou solto.', markup=False)
    console.print('Todos os outros gestos ficam bloqueados durante a rolagem. Desfazer os dois dedos '
                  'para a rolagem imediatamente; os gestos são retomados após '
                  + seconds(Control.SCROLL_COOLDOWN_SECONDS) + ' contínuos sem os dois dedos. '
                  'Falhas mais curtas mantêm o modo ativo e não repetem os avisos.', markup=False)
    return output.getvalue().rstrip()


class GesturesCommand(HelpCommand):
    def parse_args(self, ctx, args):
        return super().parse_args(ctx, args or ['start'])

    def get_help(self, ctx):
        return super().get_help(ctx) + '\n\n' + gesture_tables(ctx.terminal_width or 80)
