"""hooks, commands and filters definition."""

import os

import simplebot
from deltachat import Chat, Message
from jinja2 import Environment, PackageLoader, select_autoescape
from pkg_resources import DistributionNotFound, get_distribution
from simplebot.bot import DeltaBot, Replies

from .game import Board, pieces
from .orm import Game, init, session_scope

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "0.0.0.dev0-unknown"
template = Environment(
    loader=PackageLoader(__name__, "templates"),
    autoescape=select_autoescape(["html", "xml"]),
).get_template("board.html")


@simplebot.hookimpl
def deltabot_init(bot: DeltaBot) -> None:
    prefix = _get_prefix(bot)

    name = f"/{prefix}play"
    desc = f"Invite a friend to play Chess.\nExample:\n{name} friend@example.com"
    bot.commands.register(func=chess_play, name=name, help=desc)

    bot.commands.register(func=chess_surrender, name=f"/{prefix}surrender")
    bot.commands.register(func=chess_new, name=f"/{prefix}new")
    bot.commands.register(func=chess_repeat, name=f"/{prefix}repeat")


@simplebot.hookimpl
def deltabot_start(bot: DeltaBot) -> None:
    path = os.path.join(os.path.dirname(bot.account.db_path), __name__)
    if not os.path.exists(path):
        os.makedirs(path)
    path = os.path.join(path, "sqlite.db")
    init(f"sqlite:///{path}")


@simplebot.hookimpl
def deltabot_member_removed(bot: DeltaBot, chat: Chat) -> None:
    with session_scope() as session:
        game = session.query(Game).filter_by(chat_id=chat.id).first()  # noqa
        if game:
            members = [contact.addr for contact in chat.get_contacts()]
            players = (bot.self_contact.addr, game.p1, game.p2)
            if any(map(lambda addr: addr not in members, players)):
                session.delete(game)  # noqa
                try:
                    chat.remove_contact(bot.self_contact)
                except ValueError:
                    pass


@simplebot.filter
def filter_messages(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """To move chess pieces you must send messages in the corresponding game group.

    The message with the move must be in Standard Algebraic Notation or Long Algebraic Notation (without hyphens)
    More info about this notations can be found in Wikipedia.
    For example:
    To move pawn from e2 to e4, send a message:
    e4
    or in Long Algebraic Notation:
    e2e4
    To move knight from g1 to f3, send a message:
    Nf3
    or in Long Algebraic Notation:
    g1f3
    """
    if not message.text.replace("-", "").isalnum() or len(message.text) < 2:
        return

    with session_scope() as session:
        game = session.query(Game).filter_by(chat_id=message.chat.id).first()  # noqa
        if game is None or game.board is None:
            return

        board = Board(game.board)

        player = message.get_sender_contact().addr
        if board.turn == player:
            try:
                board.move(message.text)
                game.board = board.export()
                text, html = _run_turn(bot, game)
                replies.add(text=text, html=html)
            except (ValueError, AssertionError):
                replies.add(text="❌ Invalid move!", quote=message)


def chess_play(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    if not payload or "@" not in payload:
        prefix = _get_prefix(bot)
        replies.add(
            text=f"❌ Invalid address. Example:\n/{prefix}play friend@example.com",
            quote=message,
        )
        return

    if payload == bot.self_contact.addr:
        replies.add(text="❌ Sorry, I don't want to play", quote=message)
        return

    sender = message.get_sender_contact()
    receiver = bot.get_contact(payload)
    if sender == receiver:
        replies.add(text="❌ You can't play with yourself", quote=message)
        return

    p1, p2 = sorted([sender.addr, receiver.addr])
    with session_scope() as session:
        game = session.query(Game).filter_by(p1=p1, p2=p2).first()  # noqa
        if game is None:  # first time playing with this contact
            board = Board(p1=sender.addr, p2=receiver.addr)
            chat = bot.create_group(
                f"♞ {sender.addr} 🆚 {receiver.addr}", [sender, receiver]
            )
            game = Game(
                p1=p1,
                p2=p2,
                chat_id=chat.id,
                board=board.export(),
            )
            session.add(game)  # noqa

            text, html = _run_turn(bot, game)
            text = (
                f"Hello {receiver.name},\n"
                f"You have been invited by {sender.name} to play Chess.\n\n"
                f"{pieces['K']}: {sender.name}\n{pieces['k']}: {receiver.name}\n\n{text}"
            )
            replies.add(text=text, html=html, chat=chat)
        else:
            text = f"❌ You already have a game group with {payload}"
            replies.add(text=text, chat=bot.get_chat(game.chat_id))


def chess_surrender(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """End the Chess game in the group it is sent."""
    sender = message.get_sender_contact()
    with session_scope() as session:
        game = session.query(Game).filter_by(chat_id=message.chat.id).first()  # noqa
        if game is None or sender.addr not in (game.p1, game.p2):
            replies.add(text="❌ This is not your game group", quote=message)
        elif game.board is None:
            replies.add(text="❌ There is no active game", quote=message)
        else:
            game.board = None
            prefix = _get_prefix(bot)
            replies.add(
                text=f"🏳️ Game Over.\n{sender.name} surrenders.\n\n▶️ Play again? /{prefix}new"
            )


def chess_new(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Start a new Chess game in the current game group."""
    sender = message.get_sender_contact()
    with session_scope() as session:
        game = session.query(Game).filter_by(chat_id=message.chat.id).first()  # noqa
        if game is None or sender.addr not in (game.p1, game.p2):
            replies.add(text="❌ This is not your game group", quote=message)
        elif game.board is not None:
            replies.add(text="❌ There is an active game already", quote=message)
        else:
            p2 = bot.get_contact(game.p2 if sender.addr == game.p1 else game.p1)
            board = Board(p1=sender.addr, p2=p2.addr)
            game.board = board.export()
            text = f"▶️ Game started!\n{pieces['K']}: {sender.name}\n{pieces['k']}: {p2.name}\n\n"
            text2, html = _run_turn(bot, game)
            replies.add(text=text + text2, html=html)


def chess_repeat(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Send game board again."""
    with session_scope() as session:
        game = session.query(Game).filter_by(chat_id=message.chat.id).first()  # noqa
        html = None
        if not game:
            text = "❌ This is not a Chess game group"
        elif not game.board:
            text = "❌ There is no active game"
        else:
            text, html = _run_turn(bot, game)
        replies.add(text=text, html=html)


def _run_turn(bot: DeltaBot, game: Game) -> tuple:
    board = Board(game.board)
    result = board.result()
    if result == "*":
        text = "{} {} it's your turn...".format(
            pieces["K"] if board.turn == board.white else pieces["k"],
            bot.get_contact(board.turn).name,
        )
    else:
        game.board = None
        if result == "1/2-1/2":
            text = "🤝 Game over.\nIt is a draw!"
        else:
            if result == "1-0":
                winner = "{} {}".format(pieces["K"], bot.get_contact(board.white).name)
            else:
                winner = "{} {}".format(pieces["k"], bot.get_contact(board.black).name)
            text = "🏆 Game over.\n{} Wins!".format(winner)
        text += f"\n\n▶️ Play again? /{_get_prefix(bot)}new"
    return text, template.render(board=board, pieces=pieces)


def _get_prefix(bot: DeltaBot) -> str:
    return bot.get("command_prefix", scope=__name__) or ""
