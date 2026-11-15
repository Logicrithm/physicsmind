"""Reads a typed physics question into checked quantities before any number is calculated.

Scope today: one object launched freely under constant gravity, straight up, at an angle, or horizontally from a
raised point, landing on the ground. It can be asked for the maximum height, the time to reach the top, the time
of flight and the horizontal range, or several of these at once. The reader returns one of three verdicts:

- "solvable": every quantity was understood, each has a clear role, and the formulas apply.
- "unclear": it is one of these questions, but something is missing, ambiguous or contradictory.
  The reader says exactly what it needs. It never guesses a number, because a wrong number presented
  as checked is worse than no number.
- "not_mine": another kind of question, or a situation the formula does not cover (air resistance,
  rockets, slopes, two bodies...). The app hands these to the AI tutor, labelled as unchecked.

No model is involved: this is plain pattern reading, so the same question always gives the same verdict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re

SOLVABLE, UNCLEAR, NOT_MINE = "solvable", "unclear", "not_mine"
# What can be asked, in the order answers are given.
HEIGHT, T_TOP, T_FLIGHT, RANGE = "height", "t_top", "t_flight", "range"
ASKABLE = (HEIGHT, T_TOP, T_FLIGHT, RANGE)
ASK_NAMES = {HEIGHT: "the maximum height", T_TOP: "the time to reach the top", T_FLIGHT: "the time of flight",
             RANGE: "the horizontal range"}
EARTH_G = 9.8
SPEED_OF_LIGHT = 299_792_458.0
STANDARD_G = (9.8, 9.81, 9.807, 10.0)


@dataclass
class Quantity:
    kind: str            # speed, acceleration, length, time, angle, mass, or "" when no unit was found
    value: float         # in SI units (angles in radians)
    number: float        # as written, before conversion
    written: str         # as it appears in the question, e.g. "72 km/h"
    unit: str            # the unit as shown to the student, e.g. "km/h"; blank when none was written
    start: int
    end: int
    label: str = ""      # a symbol written just before it, e.g. "g" in "g = 10"
    role: str = ""


@dataclass
class Reading:
    status: str
    on_topic: bool = False                # the question asks for something the solver covers (or gives a maximum height)
    asks: list[str] = field(default_factory=list)         # HEIGHT, T_TOP, T_FLIGHT and/or RANGE, in ASKABLE order
    reasons: list[str] = field(default_factory=list)      # why it is unclear or not handled
    understood: list[str] = field(default_factory=list)   # what was read, in the student's words
    assumptions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    speed: Quantity | None = None         # the launch speed
    vertical_speed: Quantity | None = None  # the vertical part of the launch speed, when given directly
    angle: float | None = None            # radians
    angle_from: str = ""                  # "horizontal" or "vertical"
    angle_written: str = ""
    straight_up: bool = False             # the question itself says it goes straight up
    horizontal_launch: bool = False       # thrown horizontally: no upward speed at all
    g: float = EARTH_G
    g_written: str = ""
    launch_height: float = 0.0
    launch_height_written: str = ""
    time_to_top: Quantity | None = None
    air_resistance_neglected: bool = False


# --- Turning text into quantities ---

_REPLACEMENTS = [("²", "^2"), ("³", "^3"), ("⁻¹", "^-1"), ("⁻²", "^-2"), ("−", "-"), ("–", "-"), ("—", "-"),
                 ("×", "x"), ("·", " "), ("π", "pi"), ("θ", "theta"), ("°", " deg "), ("’", "'"), (" ", " ")]


def normalise(question: str) -> str:
    text = question
    for old, new in _REPLACEMENTS:
        text = text.replace(old, new)
    return " ".join(text.lower().split())


# (kind, pattern, factor to SI, unit as shown). Tried in order, so compound units come before their parts:
# "m/s^2" before "m/s", "km/h" before "km", "min" is reached only after "m" failed its word boundary.
UNITS = [
    ("acceleration", r"m\s*/\s*s(?:ec)?\s*\^?\s*2|m\s*/\s*s\s*/\s*s|m\s*s\s*\^?\s*-\s*2|ms\s*\^?\s*-\s*2"
                     r"|met(?:re|er)s? per second (?:squared|per second)|n\s*/\s*kg", 1.0, "m/s²"),
    ("acceleration", r"cm\s*/\s*s\s*\^?\s*2|cm\s*s\s*\^?\s*-\s*2", 0.01, "cm/s²"),
    ("acceleration", r"ft\s*/\s*s\s*\^?\s*2|(?:feet|foot) per second squared", 0.3048, "ft/s²"),
    ("speed", r"km\s*/\s*h(?:rs?|ours?)?|kmph|kmh|km\s*hr?\s*\^?\s*-\s*1|km per hour|kilomet(?:re|er)s? (?:per|an) hour",
     1000 / 3600, "km/h"),
    ("speed", r"km\s*/\s*s(?:ec)?|km\s*s\s*\^?\s*-\s*1|kilomet(?:re|er)s? (?:per|a) second", 1000.0, "km/s"),
    ("speed", r"cm\s*/\s*s(?:ec)?|cm\s*s\s*\^?\s*-\s*1|centimet(?:re|er)s? per second", 0.01, "cm/s"),
    ("speed", r"m\s*/\s*s(?:ecs?|econds?)?|m\s*s\s*\^?\s*-\s*1|ms\s*\^?\s*-\s*1|mps|met(?:re|er)s? (?:per|a) second",
     1.0, "m/s"),
    ("speed", r"mph|miles? (?:per|an) hour", 0.44704, "mph"),
    ("speed", r"ft\s*/\s*s|(?:feet|foot) per second", 0.3048, "ft/s"),
    ("speed", r"knots?", 1852 / 3600, "knots"),
    ("length", r"km|kilomet(?:re|er)s?", 1000.0, "km"),
    ("length", r"cm|centimet(?:re|er)s?", 0.01, "cm"),
    ("length", r"mm|millimet(?:re|er)s?", 0.001, "mm"),
    ("length", r"m|met(?:re|er)s?", 1.0, "m"),
    ("length", r"ft|feet|foot", 0.3048, "ft"),
    ("time", r"s|secs?|seconds?", 1.0, "s"),
    ("time", r"mins?|minutes?", 60.0, "min"),
    ("time", r"hrs?|hours?|h", 3600.0, "h"),
    ("angle", r"deg(?:rees?)?", math.pi / 180, "°"),
    ("angle", r"rad(?:ians?)?", 1.0, "rad"),
    ("mass", r"kg|kilograms?|kilos?", 1.0, "kg"),
    ("mass", r"mg|milligrams?", 1e-6, "mg"),
    ("mass", r"g|gm|grams?|grammes?", 1e-3, "g"),
]
_UNIT_PATTERNS = [(kind, re.compile(rf"(?:{pattern})(?![a-z0-9])"), factor, shown) for kind, pattern, factor, shown in UNITS]
SI_UNIT = {"speed": "m/s", "acceleration": "m/s²", "length": "m", "time": "s", "angle": "rad", "mass": "kg"}

# A number not glued to a word, an exponent or another number: "s^-2" and "m/s2" hold no number of their own.
NUMBER = re.compile(r"(?<![a-z0-9.^_/-])(-?\d+(?:,\d{3})*(?:\.\d+)?|-?\.\d+)(?:e(-?\d+)|\s*x\s*10\s*\^\s*(-?\d+))?")
PI = re.compile(r"(?<![a-z0-9.])(\d+(?:\.\d+)?)?\s*\*?\s*pi\b(?:\s*/\s*(\d+(?:\.\d+)?))?(?:\s*(?:rad(?:ians?)?)(?![a-z]))?")
LABEL = re.compile(r"(?:^|[^a-z_])(u_?y|u_?x|u|v|g|a|h|t|theta|alpha)\s*(?:=|:)\s*$")
G_WORDS = re.compile(r"(?:\bg|gravity|gravitational acceleration|acceleration (?:due to|of) gravity)"
                     r"\s*(?:=|:|is|as|of|to be|equal to|equals)?\s*(?:about\s+|approximately\s+|~\s*)?$")
ANGLE_WORDS = re.compile(r"\b(?:angle|theta|alpha|elevation)\b[^.,;\d]{0,30}$")
SPEED_WORDS = re.compile(r"\b(?:velocity|speed)\b[^.,;\d]{0,20}$")
LENGTH_WORDS = re.compile(r"\b(?:height|distance|high|tall)\b[^.,;\d]{0,20}$")
TIME_WORDS = re.compile(r"\b(?:time|after|for|takes?|in)\b[^.,;\d]{0,12}$")
AMBIGUOUS_UNITS = {"ms": "“ms” could mean milliseconds or metres per second."}


def _label(before: str) -> str:
    found = LABEL.search(before)
    if found:
        return found.group(1).replace("_", "")
    if G_WORDS.search(before[-45:]):
        return "g"
    return ""


def quantities(text: str) -> tuple[list[Quantity], list[str]]:
    """Every number in the question with its unit converted to SI, and a reason for each one that cannot be read."""
    found: list[Quantity] = []
    problems: list[str] = []
    taken: list[tuple[int, int]] = []
    for match in PI.finditer(text):
        if "pi" not in match.group():
            continue
        value = float(match.group(1) or 1) * math.pi / float(match.group(2) or 1)
        found.append(Quantity("angle", value, value, match.group().strip(), "rad", match.start(), match.end(),
                              _label(text[:match.start()])))
        taken.append(match.span())
    for match in NUMBER.finditer(text):
        if any(start <= match.start() < end for start, end in taken):
            continue
        number = float(match.group(1).replace(",", ""))
        exponent = match.group(2) or match.group(3)
        if exponent:
            number *= 10 ** int(exponent)
        rest = text[match.end():]
        gap = len(rest) - len(rest.lstrip())
        label = _label(text[:match.start()])
        for kind, pattern, factor, shown in _UNIT_PATTERNS:
            unit = pattern.match(rest, gap)
            if unit:
                end = match.end() + unit.end()
                found.append(Quantity(kind, number * factor, number, text[match.start():end], shown, match.start(), end, label))
                break
        else:
            word = re.match(r"\s*([a-z]+)(\s*(?:/|per\b))?", rest)
            if word and (word.group(1) in AMBIGUOUS_UNITS or word.group(2)):
                problems.append(AMBIGUOUS_UNITS.get(word.group(1), f"I don't recognise the unit in “{text[match.start():match.end() + word.end()].strip()}”.")
                                + " Please write it as m/s, km/h, m, s or degrees.")
                continue
            found.append(Quantity("", number, number, match.group(), "", match.start(), match.end(), label))
    found.sort(key=lambda q: q.start)
    return found, problems


def _window(text: str, quantity: Quantity, before: int = 70, after: int = 50) -> tuple[str, str]:
    """The words around a quantity, kept inside its own sentence."""
    left = text[max(0, quantity.start - before):quantity.start]
    right = text[quantity.end:quantity.end + after]
    left = re.split(r"[.;?!]\s", left)[-1]
    right = re.split(r"[.;?!](?:\s|$)", right)[0]
    return left, right


# --- What is being asked, and does the formula apply? ---

ASK = re.compile(r"\b(?:find|calculate|determine|compute|work out|estimate|evaluate|obtain|what|how|deduce|show that)\b|\?")
HEIGHT_PHRASE = re.compile(r"\b(?:max(?:imum)?\.?|greatest|highest|peak)\s+(?:vertical\s+)?(?:height|altitude)\b"
                           r"|\bhighest point\b|\bhow high\b|\bheight to which\b"
                           r"|\bheight (?:that |which )?(?:it |the \w+ )?(?:reaches|reached|attained|rises to|goes up to)\b")
# A maximum height stated as a fact ("reaches a maximum height of 20 m"), as opposed to one being asked for.
# "From a height of 20 m" is a starting point, not this.
HEIGHT_GIVEN = re.compile(r"(?:max(?:imum)?\.?|greatest|peak)\s+(?:vertical\s+)?height\s*(?:reached\s+|attained\s+)?(?:of|is|=|was|will be)\s*(?:about\s+)?-?\d"
                          r"|highest point\s*(?:is|=|of|was)\s*-?\d|\brises? to (?:a height of )?-?\d")

# The other quantities the solver answers, added 15 Nov 2026. A phrase is removed from the sentence once matched, so
# "the time to reach the maximum height" is a time question, not also a height question.
_TOP = (r"(?:its |the )?(?:max(?:imum)?\.? (?:height|point)|greatest height|highest (?:point|position)"
        r"|top(?: of (?:its|the) (?:path|flight|trajectory|motion))?|peak)\b")
_REACH_TOP = (r"(?:reach(?:es|ing)?|gets? to|getting to|rises? to|rising to|attains?|attaining|arrives? at|goes up to|go up to)"
              rf"\s+{_TOP}")
_UNTIL = r"(?:(?:to|until|till|before|for)\s+(?:it\s+|the\s+\w+\s+)?(?:to\s+)?)"
_GROUND = r"(?:the\s+)?(?:ground|floor|earth|sea|water|river|beach|road|street|surface)\b(?:\s+(?:below|level))?"
_LAND = (rf"(?:(?:hits?|hitting|strikes?|striking|reach(?:es|ing)?|gets? (?:back )?to|lands? (?:on|in|at)|"
         rf"falls? (?:back )?(?:down )?(?:to|on|onto|into)|comes? (?:back )?down (?:to|on)|returns? to|touch(?:es)?)\s+{_GROUND}"
         r"|lands?\b|landing\b|touches down\b|comes? (?:back )?down\b)")
_BACK = r"(?:return\w*|comes? back|coming back|gets? back|fall\w* back)\b"
_NOT_GIVEN = r"(?!\s*(?:is|=|was|of|equals)\s*-?\d)"  # "the time of flight is 4 s" gives a time; it doesn't ask for one
ASK_PATTERNS = {
    T_TOP: re.compile(rf"(?:\btime (?:of|for) (?:ascent|rise|rising|going up)\b|\btime to (?:the )?top\b"
                      rf"|\b(?:time|how long)\b[^.?!;]{{0,30}}?\b{_UNTIL}?{_REACH_TOP}"
                      rf"|\bwhen (?:does|will|would|did) (?:it|the \w+) {_REACH_TOP}){_NOT_GIVEN}"),
    T_FLIGHT: re.compile(rf"(?:\b(?:total )?time of flight\b|\bflight time\b"
                         r"|\btotal time\b(?: (?:taken|of (?:motion|flight)|(?:it )?(?:spends|spent|stays|is) in the air))?"
                         r"|\btime (?:it (?:spends|stays|remains|is) |spent |that it (?:spends|is) )?(?:in the air|in flight|airborne|aloft)\b"
                         r"|\bhow long\b[^.?!;]{0,40}?\b(?:in the air|in flight|airborne|aloft)\b"
                         rf"|\b(?:time|how long)\b[^.?!;]{{0,30}}?\b{_UNTIL}?(?:{_LAND}|{_BACK})"
                         rf"|\bwhen (?:does|will|would|did) (?:it|the \w+) {_LAND}){_NOT_GIVEN}"),
    RANGE: re.compile(r"(?:\b(?:horizontal )?range\b(?! of (?:speeds|values|angles|numbers))"
                      r"|\bhorizontal distance\b(?: (?:travelled|traveled|covered|moved|gone))?"
                      r"|\bdistance (?:travelled |traveled |covered |moved )?horizontally\b"
                      rf"|\bhow far\b(?!\s+(?:up|above|below|down|high))[^.?!;]{{0,50}}?\b(?:horizontally|away|{_LAND})"
                      r"|\bhow far (?:does|will|would|did) (?:it|the \w+) (?:go|travel)\b(?!\s+(?:up|down|vertically))"
                      r"|\bdistance (?:from|away from) (?:the )?(?:base|foot|bottom|edge)\b"
                      r"|\bwhere (?:does|will|would|did) (?:it|the \w+) land\b)"
                      # "The horizontal distance at that moment" (at the top, after 2 s...) is not where it lands.
                      r"(?![^.?!;]{0,40}\b(?:at (?:that|this|the same) (?:moment|time|instant|point)"
                      r"|at the (?:top|highest point|maximum height|peak)|when it (?:is at|reaches|gets to)|after \d|in \d|by the time))"),
}
# "Find the maximum height and the time taken to reach it": "it" is the height named in the same sentence.
TOP_TIME_OF_IT = re.compile(r"\b(?:time|how long)\b[^.?!;]{0,30}?\b(?:to|until|before)\s+(?:it\s+)?reach(?:es)?\s+"
                            r"(?:it|there|this point|that point|that height|this height)\b")
# Back to where it started, not down to the ground: the same thing only when it starts from the ground.
BACK_TO_START = re.compile(rf"\b{_BACK}(?!\s+(?:down\s+)?(?:to|on|onto)\s+{_GROUND})")
# Asks the solver can't answer yet. These are looked for first, because "the maximum range" also contains "range".
OTHER_ASKS_FIRST = {
    "the greatest possible range (which needs the best angle first)":
        re.compile(r"\b(?:maximum|max\.?|greatest|largest|longest|biggest) (?:possible )?(?:horizontal )?range\b"),
}
OTHER_ASKS = {
    "a time": re.compile(r"\bhow long\b|\b(?:find|calculate|determine|compute|what is|and)\s+(?:the\s+|its\s+)?(?:total\s+)?(?:time|duration)\b"
                         r"|\btime (?:taken|of flight|required|needed)\b(?!\s*(?:is|=|was|of)\s*\d)"),
    "a distance or range": re.compile(r"\brange\b|\bhow far\b|\bdistance\b|\bdisplacement\b"),
    "a speed or velocity": re.compile(r"\bwith what (?:velocity|speed)\b|\bwhat (?:velocity|speed)\b|\bhow fast\b"
                                      r"|\b(?:find|calculate|determine|compute|and)\s+(?:the\s+|its\s+)?(?:initial\s+|final\s+|minimum\s+|launch\s+|impact\s+)?(?:velocity|speed)\b"
                                      r"|\b(?:velocity|speed) (?:at the (?:top|highest point)|on (?:reaching|hitting|landing)|when it|just before)\b"),
    "an energy, force or momentum": re.compile(r"\benergy\b|\bmomentum\b|\bforce\b|\bpower\b|\bwork done\b"),
    "an angle": re.compile(r"\b(?:find|calculate|determine|what is)\s+(?:the\s+)?angle\b|\bat what angle\b"),
    "an acceleration": re.compile(r"\b(?:find|calculate|determine|what is)\s+(?:the\s+|its\s+)?acceleration\b"),
}

AIR_NEGLECTED = re.compile(r"\b(?:neglect\w*|ignor\w*|negligible|without|no|free from|disregard\w*)\b[^.;]{0,20}\b(?:air resistance|air drag|drag|air friction)\b"
                           r"|\b(?:air resistance|air drag|drag|air friction)\b[^.;]{0,15}\b(?:is|are|can be|may be)\s+(?:neglected|ignored|negligible)\b"
                           r"|\bin (?:a )?vacuum\b")
OUTSIDE = [  # situations this formula does not describe, with the reason given to the student
    (re.compile(r"\b(?:air resistance|air drag|drag|air friction|resistive force|terminal velocity)\b"), "it involves air resistance, which this formula leaves out"),
    (re.compile(r"\b(?:rocket|engine|thrust|fuel|propel\w*|motor)\b"), "something keeps pushing it (a rocket or engine), so gravity is not the only force"),
    (re.compile(r"\b(?:incline\w*|ramp|slope)\b"), "it moves along a slope, not freely through the air"),
    (re.compile(r"\b(?:pendulum|spring|string|rope|thread)\b"), "it is attached to something (a string, rope or spring)"),
    (re.compile(r"\b(?:balloon|buoyan\w*|floats?)\b"), "buoyancy acts on it, not only gravity"),
    (re.compile(r"\b(?:charged|charge of|electric|magnetic|electron|proton|ion)\b"), "electric or magnetic forces act on it"),
    (re.compile(r"\b(?:lift|elevator|moving (?:train|car|bus|truck|platform|vehicle)|from a moving)\b"), "it is launched from something that is itself moving"),
    (re.compile(r"\b(?:bounces?|rebounds?|restitution)\b"), "it bounces, which this formula does not cover"),
    (re.compile(r"\b(?:rolls?|rolling|slides?|sliding|friction)\b"), "it rolls or slides, so it is not in free flight"),
    (re.compile(r"\b(?:to clear|just clear|clears|clearing|over (?:a|the) (?:wall|fence|net|hurdle|tree)|hits? (?:a|the) (?:wall|target))\b"),
     "it has to clear or hit an obstacle, which needs more than the maximum height"),
    (re.compile(r"\b(?:lands?|landing|falls?|hits?|strikes?)\s+(?:on|onto|at|in|into)\s+(?:(?:a|an|the|another|its|top of)\s+)*"
                r"(?:(?!of\b)\w+\s+){0,2}?(?:roof|rooftop|platform|hill|building|wall|table|ledge|cliff|balcony|tower|tree|shelf"
                r"|step|terrace|window|truck|lorry|car|basket|hoop|bucket|box)\b"
                r"|\blands?\b[^.;]{0,40}\b(?:above|below|higher than|lower than)\s+(?:the |its )?(?:launch|starting|initial|point of)"),
     "it lands at a different level (on a roof, a table, a hill...), which the checked solver doesn't handle yet"),
    (re.compile(r"\b(?:two|both|another|each other|relative|second (?:ball|stone|object|body|particle|car|one)|\d+\s+(?:balls|stones|objects|bodies|particles|cars))\b"),
     "more than one object is involved"),
]
OTHER_WORLD = re.compile(r"\b(?:moon|mars|jupiter|venus|mercury|saturn|uranus|neptune|pluto|planet|asteroid|comet|space station|another world)\b")

# "Vertically" alone counts as upward only when nothing says downward: "thrown vertically downward" is down.
UP = re.compile(r"\b(?:vertically upwards?|vertically up|straight up(?:wards?)?|upwards?|up into the air|thrown up|throws? (?:\w+ ){0,2}up"
                r"|projected up|launched up|kicked up|tossed up|shot up|fired up|goes up|moving up)\b")
DOWN = re.compile(r"\b(?:downwards?|vertically down|straight down|dropped|drops|released from rest|let go|falls? from|thrown down)\b")
# Thrown horizontally. Only next to a launch word: "how far does it travel horizontally?" asks for the range instead.
SIDEWAYS = re.compile(r"\b(?:throws?|thrown|threw|projected|launched|fired|kicked|hit|shot|tossed|flung|struck|released|leaves?"
                      r"|left|directed|aimed|point(?:s|ed|ing)|jumps?|jumped|runs? off|ran off|driven)\b[^.;?]{0,40}?\bhorizontally\b"
                      r"|\bhorizontally (?:with|at)\b")
AT_ANGLE = re.compile(r"\b(?:at an angle|angle of projection|angle of elevation|obliquely|at some angle)\b")
VERTICAL_WORD = re.compile(r"\bvertically\b|\bstraight up\b")

LAUNCH_POINT_BEFORE = re.compile(r"\b(?:from|off|top of|edge of|roof of|at a height of|height of)\b")
LAUNCH_POINT_AFTER = re.compile(r"\s*(?:tall|high|above (?:the )?(?:ground|floor|sea level|sea|water|surface))\b")
BELOW_POINT = re.compile(r"\s*(?:deep|below|beneath|under)\b")
# A raised launch point named without a number ("from a height", "from the roof of a building"): the answer depends on
# a height the question doesn't give. Found by the evaluation set on 15 Nov 2026 (it answered the rise only).
RAISED_START = re.compile(r"\b(?:from|off)\s+(?:a|an|the|its|some)\s+(?:\w+\s+){0,2}?(?:height|top|roof|building|tower|cliff|"
                          r"window|bridge|balcony|hill|hilltop|table|platform|ledge|wall|stairs|terrace|mountain)\b")
TOP_TIME = re.compile(r"\b(?:reach\w*|gets? to|arriv\w* at|at)\s+(?:its |the )?(?:maximum height|max\.? height|highest point|top|peak)\b")


def _asked(text: str) -> tuple[list[str], list[str], bool]:
    """What the solver can answer that is asked for, what else is asked, and whether a maximum height is given instead."""
    sentences = [s for s in re.split(r"(?<=[.?!;])\s+", text) if s]
    asking = [s for s in sentences if ASK.search(s)] or sentences
    height_given = any(HEIGHT_GIVEN.search(s) for s in sentences)
    asks, others = set(), []
    for sentence in asking:
        rest = HEIGHT_GIVEN.sub(" ", sentence)
        for name, pattern in OTHER_ASKS_FIRST.items():
            if pattern.search(rest):
                others.append(name)
                rest = pattern.sub(" ", rest)
        names_height = bool(HEIGHT_PHRASE.search(rest))
        for name, pattern in ASK_PATTERNS.items():
            if pattern.search(rest):
                asks.add(name)
                rest = pattern.sub(" ", rest)
        if names_height and TOP_TIME_OF_IT.search(rest):
            asks.add(T_TOP)
            rest = TOP_TIME_OF_IT.sub(" ", rest)
        if HEIGHT_PHRASE.search(rest):
            asks.add(HEIGHT)
        others += [name for name, pattern in OTHER_ASKS.items() if pattern.search(rest)]
    return [name for name in ASKABLE if name in asks], list(dict.fromkeys(others)), height_given


# Asking to understand a formula rather than for a number. Found in the running app on 15 Nov 2026: "Explain how the
# range formula R = u² sin 2θ / g is derived" was read as a range calculation and asked for the launch speed.
DERIVE = re.compile(r"\b(?:deriv\w*|prove|proof|show that|show how)\b")
EXPLAIN = re.compile(r"\b(?:explain\w*|why|formula|expression|equation|in terms of|depends? on|how does .{0,40} change)\b")


def _wants_understanding(text: str) -> bool:
    """A derivation, or an explanation with no measured quantity (a number with a unit) to calculate with."""
    if DERIVE.search(text):
        return True
    return bool(EXPLAIN.search(text)) and not any(q.kind for q in quantities(text)[0])


def _show(value: float) -> str:
    """A number as a student would write it: 20, 20.41, 0.025."""
    if value == 0:
        return "0"
    if abs(value) >= 1e5 or abs(value) < 1e-3:
        return f"{value:.3e}"
    digits = max(0, 4 - int(math.floor(math.log10(abs(value)))) - 1)
    return f"{round(value, digits):.{digits}f}".rstrip("0").rstrip(".")


def _converted(q: Quantity) -> str:
    si = SI_UNIT.get(q.kind, "")
    if q.kind == "angle":
        degrees = f"{_show(math.degrees(q.value))}°"
        return degrees if q.unit == "°" else f"{q.written.replace('pi', 'π')} = {degrees}"
    if not q.unit:
        return q.written
    shown = f"{_show(q.number)} {q.unit}"  # "9.8 m/s^2" and "54 kmph" are shown as "9.8 m/s²" and "54 km/h"
    return shown if q.unit == si else f"{shown} = {_show(q.value)} {si}"


# --- The reader ---

def read_question(question: str) -> Reading:
    text = normalise(question)
    asks, other_asks, height_given = _asked(text)
    if asks and _wants_understanding(text):
        return Reading(NOT_MINE, on_topic=False, asks=asks,
                       reasons=["it asks how a formula comes about or why it works, not for a number"])
    if not asks:
        if height_given:
            reason = "it gives a maximum height and asks for something else"
        elif other_asks:
            reason = f"it asks for {', '.join(other_asks)}"
        else:
            reason = "it isn't a question about the maximum height, time of flight or range of a launched object"
        return Reading(NOT_MINE, on_topic=height_given, reasons=[reason])
    if other_asks:
        return Reading(NOT_MINE, on_topic=True, asks=asks,
                       reasons=[f"it also asks for {', '.join(other_asks)}, and the checked solver only answers the maximum "
                                f"height, the time to the top, the time of flight and the range so far"])

    reading = Reading(SOLVABLE, on_topic=True, asks=asks)
    flies = T_FLIGHT in asks or RANGE in asks   # it has to come down, not only go up
    reading.air_resistance_neglected = bool(AIR_NEGLECTED.search(text))
    for pattern, reason in OUTSIDE:
        if reading.air_resistance_neglected and "air resistance" in reason:
            continue
        if pattern.search(text):
            reading.status, reading.reasons = NOT_MINE, [reason]
            return reading

    found, unclear = quantities(text)
    speeds, gravities = [], []
    angles, heights, times = [], [], []
    for q in found:
        before, after = _window(text, q)
        if not q.kind:  # a bare number: its label or the words before it may still say what it is
            if q.label == "g" or G_WORDS.search(before[-45:]):
                q.kind, q.unit = "acceleration", ""
                reading.assumptions.append(f"No unit was given for g = {_show(q.number)}, so m/s² is assumed.")
            elif q.label in {"theta", "alpha"} or ANGLE_WORDS.search(before):
                if q.number <= 2 * math.pi and q.number != int(q.number):
                    unclear.append(f"The angle {q.written} has no unit: is it in degrees or radians?")
                    continue
                q.kind, q.value, q.unit = "angle", math.radians(q.number), "°"
                reading.assumptions.append(f"No unit was given for the angle {q.written}, so degrees are assumed.")
            elif q.label in {"u", "uy"}:
                q.kind, q.unit = "speed", ""
                reading.assumptions.append(f"No unit was given for {q.label} = {q.written}, so m/s is assumed.")
            elif SPEED_WORDS.search(before) or LENGTH_WORDS.search(before) or (TIME_WORDS.search(before) and TOP_TIME.search(before + after)):
                unclear.append(f"The number {q.written} has no unit. Is it in m/s, km/h, metres or seconds?")
                continue
            else:
                continue  # a question number, a count, a year: not a physical quantity
        if q.kind == "speed":
            speeds.append(q)
        elif q.kind == "acceleration":
            gravities.append(q)
        elif q.kind == "angle":
            angles.append(q)
        elif q.kind == "length":
            heights.append(q)
        elif q.kind == "time":
            times.append(q)
        elif q.kind == "mass":
            reading.notes.append(f"The mass ({q.written}) is not needed: without air resistance, every object launched "
                                 f"the same way rises to the same height.")

    # Speeds: the launch speed, or its vertical part.
    launch, vertical, stray = [], [], []
    for q in speeds:
        before, _ = _window(text, q)
        if q.label == "uy":
            vertical.append(q)
        elif q.label == "ux" or re.search(r"horizontal (?:component|part|velocity|speed)\b[^.,;]{0,40}$", before):
            unclear.append(f"{q.written} is the horizontal part of the velocity. I need the launch speed, or its vertical part.")
        # "Hits the ground at 30 m/s" is a landing speed; "hits a golf ball at 20 m/s" is the launch (fixed 15 Nov 2026, E21).
        elif q.label == "v" or re.search(r"\b(?:final|landing|impact|lands|on reaching|at the (?:top|highest point)|returns?"
                                         r"|hits (?:the )?(?:ground|floor|water|earth))\b[^.,;]{0,25}$", before):
            stray.append(q)
        elif re.search(r"vertical (?:component|part|velocity|speed)\b[^.,;]{0,40}$", before):
            vertical.append(q)  # "vertical velocity" added 15 Nov 2026 (evaluation set); checked after "at the top" etc.
        else:
            launch.append(q)
    if stray:
        unclear.append(f"Your question gives another speed ({', '.join(q.written for q in stray)}) besides the launch speed, "
                       f"and I can't tell how it fits.")
    if len(launch) + len(vertical) > 1:
        unclear.append(f"Your question gives more than one launch speed ({', '.join(q.written for q in launch + vertical)}). "
                       f"Which one is it thrown with?")
    for q in launch + vertical:
        if q.value <= 0:
            unclear.append(f"The launch speed {q.written} is zero or negative. Please give its size and say which way it is thrown.")
        elif q.value >= SPEED_OF_LIGHT:
            unclear.append(f"{q.written} is faster than light, so ordinary motion formulas don't apply.")
    reading.speed = launch[0] if len(launch) == 1 else None
    reading.vertical_speed = vertical[0] if len(vertical) == 1 else None

    # Gravity.
    g_values = []
    for q in gravities:
        before, _ = _window(text, q)
        if q.label == "g" or G_WORDS.search(before[-45:]):
            g_values.append(q)
        elif q.label == "a" and q.value < 0 and any(abs(abs(q.value) - g) < 1e-9 for g in STANDARD_G):
            g_values.append(q)
            reading.notes.append(f"a = {q.written} is gravity; the minus sign only means it points downward.")
        else:
            reading.status, reading.reasons = NOT_MINE, [f"it has an acceleration ({q.written}) other than gravity"]
            return reading
    if len({round(abs(q.value), 9) for q in g_values}) > 1:
        unclear.append(f"Your question gives different values for g ({', '.join(q.written for q in g_values)}).")
    elif g_values:
        q = g_values[0]
        reading.g = abs(q.value)
        reading.g_written = q.written if not q.unit else _converted(q)
        if not 0 < reading.g <= 300:
            unclear.append(f"g = {q.written} is not a value of gravity I can use. Please check it.")
    elif OTHER_WORLD.search(text):
        unclear.append(f"It isn't on Earth ({OTHER_WORLD.search(text).group()}), so please give the value of g to use there.")
    else:
        reading.assumptions.append("g = 9.8 m/s² is used, the usual school value, because the question doesn't give one. "
                                   "If your book uses 9.81 or 10, include it in the question.")

    # Angle and direction.
    thrown_down = "it is thrown or dropped downward, and the checked solver only handles upward and horizontal launches so far"
    upright = False  # an angle that means straight up
    if len(angles) > 1:
        unclear.append(f"Your question gives more than one angle ({', '.join(q.written for q in angles)}).")
    elif angles:
        q = angles[0]
        before, after = _window(text, q)
        nearby = before[-35:] + " " + after[:45]
        reading.angle, reading.angle_written = q.value, _converted(q)
        if re.search(r"\bbelow\s+(?:the\s+)?(?:horizontal|horizon)\b|\bdepression\b", nearby):
            if flies:
                reading.status, reading.reasons = NOT_MINE, [thrown_down]
                return reading
            unclear.append(f"It is launched {q.written} below the horizontal, so it never rises above its starting point.")
        elif re.search(r"\b(?:with|to|from|off)\s+(?:the\s+)?vertical\b", nearby):
            reading.angle_from = "vertical"
        else:
            reading.angle_from = "horizontal"
            if not re.search(r"\b(?:above|with|to|from|over|off)\s+(?:the\s+)?(?:horizontal|horizon|ground|level ground|floor)\b"
                             r"|\belevation\b|\bangle of projection\b", nearby):
                reading.assumptions.append(f"The angle {_converted(q)} is taken from the horizontal (the usual convention).")
        degrees = math.degrees(q.value)
        if reading.angle_from == "horizontal" and not 0 < degrees <= 90:
            unclear.append(f"An angle of {_show(degrees)}° above the horizontal doesn't describe an upward launch. "
                           f"Please give an angle between 0° and 90°.")
        if reading.angle_from == "vertical" and not 0 <= degrees < 90:
            unclear.append(f"An angle of {_show(degrees)}° from the vertical doesn't describe an upward launch. "
                           f"Please give an angle between 0° and 90°.")
        effective = degrees if reading.angle_from == "horizontal" else 90 - degrees
        upright = abs(effective - 90) < 1e-9
        if VERTICAL_WORD.search(text) and not upright:
            unclear.append(f"It says “vertically” but also gives an angle of {_converted(q)}. Which is it?")
        if DOWN.search(text) and not UP.search(text):
            if flies:
                reading.status, reading.reasons = NOT_MINE, [thrown_down]
                return reading
            unclear.append(f"It is thrown downward at {_converted(q)}, so it never rises above where it starts. Did you mean upward?")
    elif reading.vertical_speed is not None:
        if DOWN.search(text) and not UP.search(text):
            if flies:
                reading.status, reading.reasons = NOT_MINE, [thrown_down]
                return reading
            unclear.append("It is thrown downward, so it never rises above where it starts. Did you mean upward?")
    else:
        down, up = DOWN.search(text), UP.search(text)
        if down and not up:
            if flies:
                reading.status, reading.reasons = NOT_MINE, [thrown_down]
                return reading
            unclear.append("It is dropped or thrown downward, so it never rises above where it starts. "
                           "Did you mean thrown upward?")
        elif SIDEWAYS.search(text) and not up:
            reading.horizontal_launch = True
            if HEIGHT in asks or T_TOP in asks:
                unclear.append("Thrown horizontally, it never rises above where it starts, so there is no maximum height "
                               "(or time to reach it) above that point. Did you mean at an angle above the horizontal?")
        elif AT_ANGLE.search(text):
            unclear.append("It is launched at an angle, but the angle isn't given. Please include it, e.g. “at 30° above the horizontal”.")
        elif up:
            reading.straight_up = True
        elif VERTICAL_WORD.search(text):  # found by the evaluation set on 15 Nov 2026: it had assumed upward
            unclear.append("It says “vertically” but not whether it goes up or down. Is it thrown vertically upward?")
        elif reading.speed is not None:
            unclear.append("I can't tell which way it is thrown. Is it straight up, or at an angle above the ground (and which angle)?")

    # Lengths: only the height it is launched from has a place in this question.
    for q in heights:
        before, after = _window(text, q)
        if BELOW_POINT.match(after) or re.search(r"\b(?:pit|well|hole|trench|valley)\b", before):
            unclear.append(f"It starts {q.written} below the ground. Do you want the height above the starting point or above the ground?")
        elif LAUNCH_POINT_BEFORE.search(before) or LAUNCH_POINT_AFTER.match(after):
            if reading.launch_height_written:
                unclear.append(f"Your question gives more than one starting height ({reading.launch_height_written}, {q.written}).")
            reading.launch_height, reading.launch_height_written = q.value, _converted(q)
        else:
            unclear.append(f"I can't tell what the length {q.written} describes. If it is the height it is launched from, "
                           f"say so, e.g. “from the top of a {q.written} building”.")

    # Times: only the time to reach the top has a place.
    for q in times:
        before, after = _window(text, q)
        if TOP_TIME.search(before) or TOP_TIME.search(after):
            if reading.time_to_top is not None:
                unclear.append("Your question gives more than one time to reach the top.")
            elif q.value <= 0:
                unclear.append(f"The time {q.written} must be more than zero.")
            reading.time_to_top = q
        else:
            unclear.append(f"I can't tell what the time {q.written} measures. Only the time to reach the top fits this question.")

    raised_unknown = (not reading.launch_height_written and RAISED_START.search(text)
                      and not re.search(r"\bfrom (?:the )?(?:ground|floor)\b", text))
    if raised_unknown:
        unclear.append("It starts from a raised point, but its height isn't given. How high above the ground is it "
                       "launched from?" + ("" if flies else " (Or, if you only want the rise above the launch point, say so.)"))
    elif reading.horizontal_launch and reading.launch_height <= 0:
        unclear.append("Thrown horizontally, it starts falling straight away, so I need the height it is thrown from. "
                       "How high above the ground is it?")

    # What coming down means (added 15 Nov 2026 with the time of flight and the range).
    if RANGE in asks:
        if reading.straight_up or upright:
            unclear.append("Thrown straight up, it only goes up and down and comes back where it started, so it has no "
                           "horizontal range. Did you mean thrown at an angle? If so, please give the angle.")
        elif reading.speed is None and (reading.vertical_speed is not None or reading.time_to_top is not None):
            unclear.append("For the range I also need the sideways part of the launch speed. Please give the launch "
                           "speed and its angle.")
    if T_FLIGHT in asks and reading.launch_height > 0 and BACK_TO_START.search(text):
        unclear.append(f"It starts {reading.launch_height_written} above the ground. Do you want the time until it is back "
                       f"at that height, or until it reaches the ground?")
    if flies:
        reading.assumptions.append(f"It lands on the ground, {reading.launch_height_written} below where it was launched."
                                   if reading.launch_height > 0 else
                                   "It lands back at the height it was launched from (level ground).")

    if reading.speed is None and reading.vertical_speed is None and reading.time_to_top is None and not unclear:
        unclear.append("I couldn't find the launch speed. Please give it with its unit, e.g. “20 m/s”. "
                       "Numbers written as words aren't read yet.")
    if reading.time_to_top is not None and (reading.speed or reading.vertical_speed) and not unclear:
        _check_time_agrees(reading, unclear)

    if unclear:
        reading.status, reading.reasons = UNCLEAR, list(dict.fromkeys(unclear))
    _describe(reading)
    return reading


def vertical_launch_speed(reading: Reading) -> float | None:
    """The upward part of the launch speed, from whatever the question gave. None when only a time was given."""
    if reading.vertical_speed is not None:
        return reading.vertical_speed.value
    if reading.speed is None:
        return None
    if reading.horizontal_launch:
        return 0.0
    if reading.angle is None:
        return reading.speed.value
    if reading.angle_from == "vertical":
        return reading.speed.value * math.cos(reading.angle)
    return reading.speed.value * math.sin(reading.angle)


def horizontal_launch_speed(reading: Reading) -> float | None:
    """The sideways part of the launch speed. None when the question doesn't give it (only the vertical part or a time)."""
    if reading.speed is None:
        return None
    if reading.horizontal_launch:
        return reading.speed.value
    if reading.angle is None:
        return 0.0 if reading.straight_up else None
    if reading.angle_from == "vertical":
        return reading.speed.value * math.sin(reading.angle)
    return reading.speed.value * math.cos(reading.angle)


def _check_time_agrees(reading: Reading, unclear: list[str]) -> None:
    upward = vertical_launch_speed(reading)
    expected = upward / reading.g
    given = reading.time_to_top.value
    if abs(expected - given) > 0.02 * expected:
        unclear.append(f"The numbers disagree: launched that way it would take {_show(expected)} s to reach the top, "
                       f"but the question says {reading.time_to_top.written}. Please check them.")


def _describe(reading: Reading) -> None:
    """What was understood, in the student's own units, for the explanation and for a clarification."""
    if reading.asks:
        names = [ASK_NAMES[a] for a in reading.asks]
        reading.understood.append("Asked for: " + (names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]))
    if reading.speed is not None:
        reading.understood.append(f"Launch speed: {_converted(reading.speed)}")
    if reading.vertical_speed is not None:
        reading.understood.append(f"Vertical part of the launch speed: {_converted(reading.vertical_speed)}")
    if reading.angle is not None:
        reading.understood.append(f"Direction: {reading.angle_written} from the {reading.angle_from or 'horizontal'}")
    elif reading.speed is not None:
        reading.understood.append("Direction: straight up" if reading.straight_up else
                                  "Direction: horizontal" if reading.horizontal_launch else "Direction: not clear yet")
    if reading.time_to_top is not None:
        reading.understood.append(f"Time to reach the top: {_converted(reading.time_to_top)}")
    reading.understood.append(f"Gravity: g = {reading.g_written}" if reading.g_written else "Gravity: g = 9.8 m/s² (not given)")
    reading.understood.append(f"Starts from: {reading.launch_height_written} above the ground" if reading.launch_height_written
                              else "Starts from: its launch point (heights are measured from there)")
