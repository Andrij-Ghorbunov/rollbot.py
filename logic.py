import re
import json
import random

def get_code(match: re.Match, name: str, default):
    strcode = match.group(name)
    if strcode:
        return int(strcode)
    return default

def get_code_sp(match: re.Match, name: str, default):
    strcode = match.group(name)
    if strcode:
        return int(strcode.replace(' ', ''))
    return default

def get_code_dt(match: re.Match, name: str, default):
    strcode = match.group(name)
    if not strcode:
        return default
    if strcode[0]=='F':
        return strcode
    return int(strcode)

def get_code_b(match: re.Match, name: str):
    strcode = match.group(name)
    if strcode:
        return True
    return False

def parse_code(code):
    match = re.search(
        r"^\s*(?P<dicenum>\d*)(d(?P<dicetype>\d+|F))?(t(?P<threshold>\d+))?(?P<explode>\!)?(?P<nobotch>=)?\s*(?P<modifier>[+-]\s*\d+)?(\s*dc\s*(?P<dc>\d+))?\s*$",
        code)
    if not match:
        return None
    return {
        'dicenum': get_code(match, 'dicenum', 1),
        'dicetype': get_code_dt(match, 'dicetype', 10),
        'threshold': get_code(match, 'threshold', None),
        'explode': get_code_b(match, 'explode'),
        'nobotch': get_code_b(match, 'nobotch'),
        'modifier': get_code_sp(match, 'modifier', 0),
        'dc': get_code(match, 'dc', 1)
    }

def roll_straight(props):
    arr = []
    min = 1
    max = props['dicetype']
    if props['dicetype'] == 'F':
        min = -1
        max = 1
    for _ in range(props['dicenum']):
        arr.append(random.randint(min, max))
    arr.sort(reverse=True)
    score = props['modifier']
    t = props['threshold']
    dc = props['dc']
    isThreshold = t is not None
    if isThreshold:
        score += len(list(filter(lambda x: x >= t, arr)))
    else:
        score += sum(arr)
    explode = props['explode'] and min == 1
    canbotch = not props['nobotch'] and min == 1 and t is not None
    if explode:
        score += len(list(filter(lambda x: x == max, arr)))
    if canbotch:
        score -= len(list(filter(lambda x: x == min, arr)))
    dicearr = []
    if isThreshold:
        for d in arr:
            if d >= t:
                if explode and d == max:
                    dicearr.append(f"<b><u>{d}</u></b>")
                else:
                    dicearr.append(f"<b>{d}</b>")
            else:
                if canbotch and d == min:
                    dicearr.append(f"<i>{d}</i>")
                else:
                    dicearr.append(f"{d}")
    else:
        for d in arr:
            if explode and d == max:
                dicearr.append(f"<u>{d}</u>")
            else:
                dicearr.append(f"{d}")
    dicestr = ', '.join(dicearr)
    return {
        'score': score,
        'str': dicestr,
        'success': score >= dc,
        'overkill': score - dc if score >= dc else (0 if score >= 0 else -score)
    }

def roll_normal(props):
    pass

def roll_poisson(props):
    pass

def roll(props):
    if props['dicenum'] < 100:
        return roll_straight(props)
    if props['threshold']:
        return roll_poisson(props)
    return roll_normal(props)

def roll_code_parse(code):
    if '&' in code:
        index = code.index('&')
        roll1 = parse_code(code[:index])
        roll2 = parse_code(code[(index+1):])
        print(roll2)
        if not roll1 or not roll2:
            return None
        roll2['nobotch'] = True
        roll1result = roll(roll1)
        if roll1result['success']:
            roll2['dicenum'] += roll1result['overkill']
            roll2result = roll(roll2)
            return [roll1result, roll2result]
        return [roll1result]
    else:
        roll0 = parse_code(code)
        if not roll0:
            return None
        rollresult = roll(roll0)
        return [rollresult]

def roll_code(code):
    res = roll_code_parse(code)
    if not res:
        return "Error"
    text = res[0]['str'] + f'\r\nScore: {res[0]['score']}'
    if len(res) > 1:
        text += '\r\nDamage roll:\r\n' + res[1]['str'] + f'\r\nScore: {res[0]['score']}'
    return text



# print('\r\n\r\nStart debug session\r\n\r\n')
# print(roll_code("5d10t6! & 4d10t6"))
# print('\r\n\r\nEnd debug session\r\n\r\n')
