# Asphalt 9 macro generator
# MP mode and classic hunt   

import re

# Refill times
REFILL_D6 = 2 * 60
REFILL_D5 = 7 * 60
REFILL_D4 = 15 * 60
REFILL_C6 = 13 * 60
REFILL_C5 = 22 * 60
REFILL_C4 = 30 * 60
REFILL_B6 = 30 * 60
REFILL_B5 = 40 * 60
REFILL_B4 = 49 * 60
REFILL_B3 = 63 * 60
REFILL_A4 = 55 * 60
REFILL_A3 = 65 * 60
REFILL_S4 = 60 * 60
REFILL_S3 = 72 * 60

MACRO_RESET_TO_CAREER_CORNER = """
    LOOP 7
        B 0.5S
        1.0S
    DPAD_DOWN 3.0S
    1.0S
    DPAD_RIGHT 5.0S
    1.0S
    A 0.1S
    1.0S
    LOOP 4
        B 0.1S
        1.0S
    2.0S"""

MACRO_RESET_MOVE_TO_CAR_POS = """
    # Reset to the first car
    DPAD_DOWN 1.0S
    1.0S
    DPAD_LEFT 5.0S
    1.0S
    # Car position 
    LOOP {}
        DPAD_RIGHT 0.1S
        0.5S
    1.0S
    DPAD_{} 0.1S
    1.0S"""

MACRO_BACK_TO_HOME = """
    LOOP 7
        B 0.1S
        1.0S"""

MACRO_QUIT_RACE = """
    50.0S
    B 0.1S
    1.0S
    PLUS 0.1S
    1.0S
    DPAD_DOWN 2.0S
    A 0.1S
    5.0S
    LOOP 5
        B 0.1S
        1.0S"""

AA = """
    LOOP 2
        A 0.1S
        3.0S"""

def parse_macro(macro):

    parsed = macro.split("\n")
    parsed = list(filter(lambda s: not s.strip() == "", parsed))
    parsed = list(filter(lambda s: not s.strip().startswith("#"), parsed))
    parsed = parse_loops(parsed)
    #print(parsed)
    return parsed

def parse_loops(macro):
    parsed = []
    i = 0
    while i < len(macro):
        line = macro[i]
        if line.startswith("LOOP"):
            loop_count = int(line.split(" ")[1])
            loop_buffer = []

            # Detect delimiter and record
            if macro[i+1].startswith("\t"):
                loop_delimiter = "\t"
            elif macro[i+1].startswith("    "):
                loop_delimiter = "    "
            else:
                loop_delimiter = "  "

            # Gather looping commands
            for j in range(i+1, len(macro)):
                loop_line = macro[j]
                if loop_line.startswith(loop_delimiter):
                    # Replace the first instance of the delimiter
                    loop_line = loop_line.replace(loop_delimiter, "", 1)
                    loop_buffer.append(loop_line)
                # Set the new position if we either encounter the end
                # of the loop or we reach the end of the macro
                else:
                    i = j - 1
                    break
                if j+1 >= len(macro):
                    i = j

            # Recursively gather other loops if present
            if any(s.startswith("LOOP") for s in loop_buffer):
                loop_buffer = parse_loops(loop_buffer)
            # Multiply out the loop and concatenate
            parsed = parsed + (loop_buffer * loop_count)
        else:
            parsed.append(line)
        i += 1

    return parsed

def macro_time(macro):
   # macro: unparsed text macro
    macro_time = 0.0
    for mc in parse_macro(macro):
        time = ''
        try:
            time = re.search('.*(\d+.\d+?)S', mc).group(1)
            macro_time = macro_time + float(time)
        except AttributeError:
            #print('error')
            pass
    return int(macro_time)

def nitro(duration=168, blue_nitro = True):
    macro = """
    # Nitro loop
    LOOP {}"""
    macro_blue = """
        Y 0.1S
        0.5S"""
    macro_orange = """
        Y 0.1S
        0.1S"""
    if blue_nitro: 
        loops = int(duration // 0.6)
        macro = macro.format(loops) + macro_blue
    else: 
        loops = int(duration // 0.2)
        macro = macro.format(loops) + macro_orange

    return macro
 
def reset_move_to_car_pos(car_pos,car_row):
    macro = """
    # Reset to the first car
    DPAD_DOWN 1.0S
    1.0S
    DPAD_LEFT 5.0S
    1.0S"""
    marco_car_pos = """
    # Car position 
    LOOP {}
        DPAD_RIGHT 0.1S
        0.5S
    1.0S"""
    marco_car_row = """
    DPAD_{} 0.1S
    1.0S
    LOOP 2
        A 0.1S
        3.0S"""
    if int(car_pos) > 0:
        macro = macro + marco_car_pos.format(car_pos)

    macro = macro + marco_car_row.format(car_row)
    return macro

def mp_loop(mp_no=1, rep = 1, garage=[], race_time=168, blue_nitro=True, quit=False):
    # mp_no: select MP 1,2,3
    # MP loop. Reset car pos. to the very beginning. 
    # rep:      number of repetitions for each car
    # garage:   array of tuples [{"<car pos>:<UP/DOWN pos>}], if garage = [] it will stay at the last selected car

    macro = ''

    LOOP = """
# MP CAR 1 
LOOP {}
    # 235.5S EACH CYCLE"""

    LOOP = LOOP + MACRO_RESET_TO_CAREER_CORNER + """
    # to multiplayer section
    LOOP 4
        ZL 0.1S
        0.5S
    2.0S"""
    if mp_no > 1:
       for i in range(mp_no-1):

           LOOP = LOOP + """
    DPAD_DOWN 0.1S
    1.0S"""
    LOOP = LOOP + """
    LOOP 2
        A 0.1S
        3.0S
    3.0S"""

    if quit:
        nitro_loop = MACRO_QUIT_RACE
    else:
        nitro_loop = nitro(duration=race_time, blue_nitro=blue_nitro)

    if len(garage) != 0:
        for dic in garage:
            for pos,row in dic.items():
                macro = macro + LOOP.format(rep)  + reset_move_to_car_pos(pos, row) + nitro_loop + MACRO_BACK_TO_HOME
                #  parse_macro(LOOP.format(rep, pos, row))
    else: 
        macro = macro + LOOP.format(rep) + AA + nitro_loop + MACRO_BACK_TO_HOME

    macro = macro + "\n# MP loop duration: " + str(macro_time(macro))
    return macro

def hunt_classic(rep = 1, garage=[], event_position=5, race_time=60, blue_nitro = True):
    # Classic car hun loop. Reset car pos. to the very beginning. 
    # rep:      number of repetitions for each car
    # garage:   array of tuples [{"<car pos>:<UP/DOWN pos>}]
    # blue_nitro:  blue or orange nitro
    macro = ''
    AA = """
    LOOP 2
        A 0.1S
        3.0S"""

    LOOP = """
# HUNT CAR 
LOOP {}
    # 190S EACH RUN""" + MACRO_RESET_TO_CAREER_CORNER + """
    # to Daily section
    LOOP 5
        ZL 0.1S
        1.0S
    2.0S
    A 0.1S
    4.0S
    # EVENT POSITION
    LOOP {}
        DPAD_RIGHT 0.1S
        1.0S
    LOOP 3
        A 0.1S
        5.0S"""
    if len(garage) != 0:
        for dic in garage:
            for pos,row in dic.items():
                macro = macro + LOOP.format(rep, event_position)  + reset_move_to_car_pos(pos, row) + nitro(duration=race_time, blue_nitro=blue_nitro) + MACRO_BACK_TO_HOME
    else:
        macro = macro + LOOP.format(rep, event_position) + AA + nitro(duration=race_time, blue_nitro=blue_nitro) + MACRO_BACK_TO_HOME

    macro = macro + "\n# hunt loop duration: " + str(macro_time(macro))
    return macro


#print('LOOP 200')

td_hunt_1 = ['3.0S','DPAD_RIGHT 0.1S','1.0S','Y 0.1S','0.1S','Y 0.1S','0.1S' ]

garage_1 = [{'3':'UP'}]

garage_mp1_3_d_car_slips = [{'3':'UP'}, {'6':'UP'}, {'9':'UP'}]

garage_d_hunt = [{'8':'DOWN'}]

garage_mixed_leagues = [{'20':'DOWN'}, {'22':'UP'}, {'24':'UP'}, {'26':'DOWN'}, {'33':'UP'}, {'33':'DOWN'}, {'34':'UP'}, {'34':'DOWN'}, {'35':'UP'}, {'38':'DOWN'}, {'39':'DOWN'}]

garage_for_b_hunt = [{'20':'UP'}, {'22':'DOWN'}, {'27':'UP'}]

garage_mp2_8_cars = [{'3':'DOWN'}, {'2':'DOWN'}, {'1':'DOWN'}, {'2':'UP'}, {'0':'DOWN'}, {'1':'UP'}, {'0':'UP'}]

garage_mp2_8_cars_p1 = [{'3':'DOWN'}, {'3':'UP'}, {'2':'DOWN'}, {'1':'DOWN'}, {'2':'UP'}]
garage_mp2_8_cars_p2 = [{'0':'UP'}]

garage_mp2_13_cars = [{'7':'DOWN'}, {'6':'DOWN'}, {'6':'UP'}, {'5':'DOWN'}, {'5':'UP'}, {'4':'UP'}, {'4':'DOWN'}, {'3':'DOWN'}, {'3':'UP'}, {'2':'DOWN'}, {'2':'UP'}, {'1':'UP'}, {'1':'DOWN'}]

garage_mp1_4_c_car_classic = [{'18':'DOWN'}, {'19':'DOWN'}, {'20':'DOWN'}, {'21':'DOWN'}, {'21':'UP'} ]

garage_mp_4_c_car_classic = [{'18':'DOWN'}, {'19':'DOWN'}, {'20':'DOWN'}, {'21':'DOWN'}, {'21':'UP'} ]

garage_mp1_2_c_car_classic1 = [{'18':'UP'}, {'19':'DOWN'} ]
garage_mp_5_c_car_classic = [{'17':'UP'}, {'18':'DOWN'}, {'19':'UP'}, {'20':'UP'}, {'21':'UP'}, {'25':'DOWN'} ]


garage_mp1_2_c_car_classic2 = [{'20':'DOWN'}, {'21':'DOWN'} ]

garage_mp_3_d_car_slip = [{'10':'DOWN'}, {'10':'UP'}, {'11':'UP'}]
garage_mp_5_c_car_slip = [{'19':'DOWN'}, {'20':'UP'}, {'20':'DOWN'}, {'21':'UP'}, {'21':'DOWN'}]

garage_mp2_5_cars = [{'3':'DOWN'}, {'2':'DOWN'}, {'1':'DOWN'}, {'2':'UP'}, {'0':'DOWN'}]

out = hunt_classic(rep=1, garage=[], event_position=4, race_time=85, blue_nitro=False)
print(out)


#out = mp_loop(mp_no=1, rep=1, garage=garage_mp_5_c_car_classic, race_time=170, blue_nitro=True)
#print(out)

#out = mp_loop(mp_no=2, rep=3, garage=[], race_time=120, blue_nitro=False, quit=True)
#print(out)

#out = hunt_classic(rep=1, garage=garage_d_hunt, event_position=3, race_time=85, blue_nitro=True)
#print(out)

#out = mp_loop(mp_no=2, rep=1, garage=garage_mp1_2_c_car_classic2, race_time=120, blue_nitro=False)
#print(out)

#print(parse_macro(out))
#print(macro_time(out))
#print(600 - macro_time(out))
