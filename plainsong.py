import enum
from typing import List, Dict, Optional
import re
import json

CHORD_REGEX = '^(C|D|E|F|G|A|B)(b|#)?(m|M|min|maj|dim|Δ|°|ø|Ø)?((sus|add)?' \
              '(b|#)?(2|4|5|6|7|9|10|11|13)?)*' \
              '(\+|aug|alt)?(\/(C|D|E|F|G|A|B)(b|#)?)?$'


class SongChord:
    def __init__(self, name: str, pos: int):
        super().__init__()
        self.name = name
        self.pos = pos


class SongLine:
    def __init__(self, text: str, chords: List[SongChord] = []):
        super().__init__()
        self.text = text
        self.chords = chords


class SongPart:
    def __init__(self):
        super().__init__()
        self.name = ''
        self.lines: List[SongLine] = []

    def is_empty(self) -> bool:
        if self.name:
            return False

        if self.lines:
            return False

        return True


class Song:
    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.metadata: Dict[str, str] = dict()
        self.parts: List[SongPart] = []


class SongParser:
    class State(enum.Enum):
        START = enum.auto()
        DEFINITION = enum.auto()
        BODY = enum.auto()

    def __init__(self):
        super().__init__()
        # Result data
        self.state = SongParser.State.START
        self.song: Song = None

        # State for parsing
        self.last_chords: List[SongChord] = []
        self.part = SongPart()

    def parse_metadata(self, line: str) -> bool:
        """Determines whether a line is metadata and, if so, parses it

        Args:
            line (str): The line to parse.

        Returns:
            bool: Whether the line is metadata
        """
        matcher = re.search('^\s*(.*): (.*)\s*$', line)

        if not matcher:
            return False

        identifier = matcher.group(1)
        value = matcher.group(2)
        self.song.metadata[identifier] = value

        return True

    def parse_part(self, line: str):
        # If the current part is empty, try to interpret the line as part name
        if self.part.is_empty():
            matcher = re.search('^\s*(.*):\s*$', line)
            if matcher:
                self.part.name = matcher.group(1)
                return

        # Try to interpret as chord line
        if self.is_chord_line(line):
            chords = self.parse_chords(line)

            # If the last line had chords, then put them on their own line
            if self.last_chords:
                self.part.lines.append(SongLine('', self.last_chords))

            # Save the chords to be over the next line
            self.last_chords = chords
            return

        # If the line is not a chord line, then save it with its chords
        else:
            self.part.lines.append(SongLine(line, self.last_chords))
            if self.last_chords:
                self.last_chords = []
            return

    @staticmethod
    def is_chord_line(line: str) -> bool:
        """Determines whether every word in a line is a chord

        Args:
            line (str): The line to check.

        Returns:
            bool: If every word in a line is a chord
        """
        for word in line.split(' '):
            if not word:
                continue
            if re.match(CHORD_REGEX, word) is None:
                return False

        return True

    @staticmethod
    def parse_chords(line: str) -> List[SongChord]:
        pos = 0
        start = 0
        chord = ''
        chords: List[SongChord] = []

        for char in line:
            if char == ' ':
                if chord:
                    chords.append(SongChord(chord, start))
                    chord = ''
            else:
                if not chord:
                    start = pos
                chord = chord + char

            pos = pos + 1

        if chord:
            chords.append(SongChord(chord, start))

        return chords

    def parse_line(self, line: str):
        stripped_line = line.strip()

        if self.state == SongParser.State.START:
            # Ignore any leading blank lines
            if stripped_line == '':
                return

            # The first line with content is the song title
            self.song = Song(stripped_line)
            self.state = SongParser.State.DEFINITION
            return

        elif self.state == SongParser.State.DEFINITION:
            # Ignore blank lines
            if stripped_line == '':
                return

            # Parse either meta data or the first song part
            if not self.parse_metadata(line):
                self.state = SongParser.State.BODY
                self.parse_part(line)

        elif self.state == SongParser.State.BODY:
            # If there is a blank line, push any non empty part and reset it
            if stripped_line == '':
                if not self.part.is_empty():
                    if self.last_chords:
                        self.part.lines.append(SongLine('', self.last_chords))
                    self.song.parts.append(self.part)
                    self.part = SongPart()

                return

            # Otherwise parse the line to the current part
            self.parse_part(line)
            return


def parse_song_file(filename: str) -> Song:
    parser = SongParser()

    with open(filename, 'r') as file:
        for line in file:
            parser.parse_line(line[:-1])

    parser.parse_line('')

    return parser.song


song = parse_song_file('test.song')
print(json.dumps(song.__dict__, sort_keys=True, indent=4,
                 default=lambda o: o.__dict__))
