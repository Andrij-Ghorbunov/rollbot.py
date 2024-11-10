import re
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

def validate_props(props):
    isFate = str(props['dicetype'])[0] == 'F'
    if isFate:
        props['explode'] = False
        props['nobotch'] = True
        props['forcebotch'] = False
        props['threshold'] = None
    elif props['dicetype'] < 1:
        props['dicetype'] = 1
    return props

def parse_code(code):
    match = re.search(
        r"^\s*(?P<dicenum>\d*)(d(?P<dicetype>\d+|F))?(t(?P<threshold>\d+))?(?P<explode>\!)?(?P<nobotch>=)?(?P<forcebotch>\?)?\s*(?P<modifier>[+-]\s*\d+)?(\s*[Dd][Cc]\s*(?P<dc>\d+))?",
        code)
    if not match:
        return None
    return validate_props({
        'dicenum': get_code(match, 'dicenum', 1),
        'dicetype': get_code_dt(match, 'dicetype', 10),
        'threshold': get_code(match, 'threshold', None),
        'explode': get_code_b(match, 'explode'),
        'nobotch': get_code_b(match, 'nobotch'),
        'forcebotch': get_code_b(match, 'forcebotch'),
        'modifier': get_code_sp(match, 'modifier', 0),
        'dc': get_code(match, 'dc', 1)
    })

def unparse(props):
    if not props:
        return ''
    dicenum = props['dicenum']
    dicetype = props['dicetype']
    t = props['threshold']
    explode = props['explode']
    nobotch = props['nobotch'] and not props['forcebotch']
    modifier = props['modifier']
    dc = props['dc']
    r = f'{dicenum}d{dicetype}'
    if t is not None:
        r += f't{t}'
    if explode:
        r += '!'
    if nobotch and t is not None:
        r += '='
    if modifier:
        if modifier > 0:
            r += f'+{modifier}'
        else:
            r += f'{modifier}'
    if t is None or dc != 1:
        r += f' dc {dc}'
    return r

def unparse_full(props):
    if not props:
        return ''
    dicenum = props['dicenum']
    dicetype = props['dicetype']
    t = props['threshold']
    explode = props['explode']
    nobotch = props['nobotch'] and not props['forcebotch']
    modifier = props['modifier']
    dc = props['dc']
    r = f'{dicenum}d{dicetype}'
    if modifier:
        if modifier > 0:
            r += f' + {modifier}'
        else:
            r += f' - {-modifier}'
    if t is not None:
        r += f', threshold {t}'
    if explode:
        r += f', {dicetype}s explode'
    if nobotch and t is not None:
        r += ', no botch'
    if t is None or dc != 1:
        r += f', DC {dc}'
    return r

def get_fate_score(score):
    if score <= -2:
        return "Terrible"
    if score >= 9:
        return "Beyond Legendary"
    match score:
        case -1: return "Poor"
        case 0: return "Mediocre"
        case 1: return "Average"
        case 2: return "Fair"
        case 3: return "Good"
        case 4: return "Great"
        case 5: return "Superb"
        case 6: return "Fantastic"
        case 7: return "Epic"
        case 8: return "Legendary"
    return "?"

def roll_straight(props):
    arr = []
    min = 1
    max = props['dicetype']
    isFate = str(props['dicetype'])[0] == 'F'
    if isFate:
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
    canbotch = (not props['nobotch'] and min == 1 and t is not None) or props['forcebotch']
    if explode:
        score += len(list(filter(lambda x: x == max, arr)))
    if canbotch:
        score -= len(list(filter(lambda x: x == min, arr)))
    dicearr = []
    if isFate:
        for d in arr:
            if d > 0:
                dicearr.append("+")
            elif d < 0:
                dicearr.append("-")
            else:
                dicearr.append("0")
    elif isThreshold:
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
    description = None
    if isFate:
        description = get_fate_score(score)
    return {
        'score': score,
        'str': dicestr,
        'success': score >= dc,
        'overkill': score - dc if score >= dc else (0 if score >= 0 else -score),
        'description': description
    }

def roll_normal(props):
    pass

def roll_poisson(props):
    pass

def roll_internal(props):
    if props['dicenum'] <= 100:
        return roll_straight(props)
    if props['threshold']:
        return roll_poisson(props)
    return roll_normal(props)

def roll(props):
    res = roll_internal(props)
    if not res:
        return None
    res['unparse'] = unparse(props)
    res['unparse_full'] = unparse_full(props)
    return res

def roll_result_to_str(res):
    r = res['unparse_full'] + ':\r\n'
    r += res['str'] + '\r\n'
    score = res['score']
    overkill = res['overkill']
    description = res['description']
    if description:
        r += f'<b>{description}</b>'
    elif res['success']:
        r += f'<b>Success</b> by {overkill}'
    elif score < 0:
        r += f'<b>Botch</b> by {overkill}'
    else:
        r += '<b>Fail</b>'
    r += f'\r\nScore: {score}'
    return r

def roll_code_parse(code):
    if '&' in code:
        index = code.index('&')
        roll1 = parse_code(code[:index])
        roll2 = parse_code(code[(index+1):])
        if not roll1 or not roll2:
            return None
        # roll2['nobotch'] = True # uncomment for auto-nobotch for damage roll
        roll1result = roll(roll1)
        if roll1result['success']:
            bonus = 0
            if roll2['threshold']:
                roll2['dicenum'] += roll1result['overkill']
                bonus = roll1result['overkill']
            roll2result = roll(roll2)
            roll2result['bonus'] = bonus
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
        return None
    text = roll_result_to_str(res[0])
    if len(res) > 1:
        text += '\r\n\r\nDamage roll'
        bonus = res[1]['bonus']
        if bonus:
            text += f' ({bonus} extra dice from hit successes)'
        text += ':\r\n' + roll_result_to_str(res[1])
    return text



# print('\r\n\r\nStart debug session\r\n\r\n')
# print(roll_code('7dF'))
# print('\r\n\r\nEnd debug session\r\n\r\n')
