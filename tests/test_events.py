from birdie.events import new_player_events, parse_event
from birdie.models import Event


def test_parse_champion_kill_normalises_killer_to_actor() -> None:
    raw = {
        "EventID": 5,
        "EventName": "ChampionKill",
        "EventTime": 123.4,
        "KillerName": "Me#EUW",
        "VictimName": "Them#EUW",
        "Assisters": ["Ally#EUW"],
    }

    event = parse_event(raw)

    assert event == Event(
        id=5,
        name="ChampionKill",
        game_time=123.4,
        actor="Me#EUW",
        victim="Them#EUW",
        assisters=("Ally#EUW",),
    )


def test_parse_multikill_reads_kill_streak() -> None:
    raw = {
        "EventID": 9,
        "EventName": "Multikill",
        "EventTime": 200.0,
        "KillerName": "Me#EUW",
        "KillStreak": 3,
    }

    event = parse_event(raw)

    assert event is not None
    assert event.name == "Multikill"
    assert event.actor == "Me#EUW"
    assert event.kill_streak == 3


def test_parse_maps_recipient_and_acer_to_actor() -> None:
    first_blood = parse_event(
        {"EventID": 1, "EventName": "FirstBlood", "EventTime": 60.0, "Recipient": "Me#EUW"}
    )
    ace = parse_event(
        {"EventID": 2, "EventName": "Ace", "EventTime": 300.0, "Acer": "Me#EUW"}
    )

    assert first_blood is not None and first_blood.actor == "Me#EUW"
    assert ace is not None and ace.actor == "Me#EUW"


def test_new_player_events_keeps_only_events_involving_the_player() -> None:
    player = "Me#EUW"
    batch = [
        {"EventID": 0, "EventName": "GameStart", "EventTime": 0.0},
        {"EventID": 1, "EventName": "ChampionKill", "EventTime": 10.0,
         "KillerName": "Me#EUW", "VictimName": "X"},
        {"EventID": 2, "EventName": "ChampionKill", "EventTime": 12.0,
         "KillerName": "Rando", "VictimName": "Other"},
        {"EventID": 3, "EventName": "ChampionKill", "EventTime": 20.0,
         "KillerName": "Z", "VictimName": "Me#EUW"},
        {"EventID": 4, "EventName": "ChampionKill", "EventTime": 25.0,
         "KillerName": "W", "VictimName": "V", "Assisters": ["Me#EUW"]},
    ]

    events = new_player_events(batch, player, seen_ids=set())

    assert [e.id for e in events] == [1, 3, 4]


def test_new_player_events_skips_already_seen_ids() -> None:
    player = "Me#EUW"
    batch = [
        {"EventID": 1, "EventName": "ChampionKill", "EventTime": 10.0,
         "KillerName": "Me#EUW", "VictimName": "X"},
        {"EventID": 2, "EventName": "ChampionKill", "EventTime": 20.0,
         "KillerName": "Me#EUW", "VictimName": "Y"},
    ]

    events = new_player_events(batch, player, seen_ids={1})

    assert [e.id for e in events] == [2]
