import re
import random
import numpy
import scipy
import scipy.special
import math

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
    if props['threshold'] is not None and props['dc'] is None:
        props['dc'] = 1 # 1 success required in order to count a threshold roll successful
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
        'dc': get_code(match, 'dc', None)
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
    if dc is not None and (t is None or dc != 1):
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
    if dc is not None and (t is None or dc != 1):
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

def result_success(score, dc) -> bool:
    if dc is None:
        return True
    return score >= dc

def result_overkill(score, dc):
    if dc is None:
        return None
    return score - dc if score >= dc else (0 if score >= 0 else -score)

def dice_str_array(arr, min, max, isFate, t, explode, canbotch):
    dicearr = []
    if isFate:
        for d in arr:
            if d > 0:
                dicearr.append("+")
            elif d < 0:
                dicearr.append("-")
            else:
                dicearr.append("0")
    elif t is not None:
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
    return dicearr

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
    dicearr = dice_str_array(arr, min, max, isFate, t, explode, canbotch)
    dicestr = ', '.join(dicearr)
    description = None
    if isFate:
        description = get_fate_score(score)
    return {
        'score': score,
        'str': dicestr,
        'success': result_success(score, dc),
        'overkill': result_overkill(score, dc),
        'title': None,
        'description': description
    }

# This function uses inverse error function in order to convert a uniformly distributed variable s
# into another variable m distributed normally. The parameters of the desired normal distribution
# are given with number of tries n and chance of success in a single try p, so that the obtained
# normal distribution is the best approximation for the corresponding binomial distribution
# (per de Moivre–Laplace theorem).
# In short, this gives us the number of times an event occured in n attempts, but with a single
# call to the random number generator.
def roll_inverse_normal_s(n, p, s):
    erfi = scipy.special.erfinv(2*s-1) # erfi is normal with center 0 and standard deviation 1
    m = n*p + erfi*math.sqrt(n*p*(1-p)) # center + erfi * needed standard deviation
    if m < 0: # clamp to limits
        m = 0
    if m > n:
        m = n
    return math.trunc(m + 0.5) # round to nearest integer

def roll_inverse_normal(n, p):
    s = random.random() # 2s-1 is uniform on [-1..1]
    return roll_inverse_normal_s(n, p, s)

# This function uses Poisson theorem to approximate binomial distribution
# in case of small n*p (math. expectation of number of successes), similarly to
# the previous function using de Moivre–Laplace theorem.
# Falls back to de Moivre–Laplace where it is expected to give a more
# accurate approximation (happens no more than 1 time in a million).
def roll_inverse_poisson_s(n, p, s):
    running_total = 0 # cumulative distribution function value
    lmbd = n*p #lambda
    lmbd_m = 1 # lambda to the power of m
    e_minlmbd = math.exp(-lmbd) # e^-lambda
    factinv = 1 # 1/m!
    for m in range(10): # only 10 to 20 first values will actually be better than normal distribution
        # (but they still cover 99.9999% of use cases)
        running_total += lmbd_m * e_minlmbd * factinv # add current member
        if s < running_total: # reached the Poisson distribution threshold
            return m # no need for further calculations, we're there
        lmbd_m *= lmbd # increase power of lambds
        factinv /= m + 1 # increase factorial in the denominator
    # if s is so high, normal distribution by de Moivre–Laplace is better
    # The benchmark showed that s here must be at least 0.999999
    return roll_inverse_normal_s(n, p, s)

def roll_inverse_poisson(n, p):
    s = random.random() # uniform on [0..1]
    return roll_inverse_poisson_s(n, p, s)

# Similar to roll_inverse_normal, this function rolls an entire array of all k possible outcomes with 1/k probability each.
# It renormalizes any exceeding values, so that the sum of the resulting array is exactly n. 
def roll_inverse_normal_arr(n, k):
    p = 1 / k
    m = []
    mtotal = 0
    for _ in range(k):
        s = random.random() # 2s-1 is uniform on [-1..1]
        erfi = scipy.special.erfinv(2*s-1) # erfi is normal with center 0 and standard deviation 1
        mcurr = 0.5 + n*p + erfi*math.sqrt(n*p*(1-p)) # center + erfi * needed standard deviation
        mtotal += mcurr
        m.append(mcurr)
    if mtotal <= 0: # a very unlikely situation
        return []
    factor = n / mtotal # first normalize by the total rolled value
    res = []
    res_sum = 0
    for x in m:
        normalized_x = x * factor
        if normalized_x < 0:
            normalized_x = 0
        if normalized_x > n:
            normalized_x = n
        trunc_x = math.trunc(normalized_x + 0.5)
        res_sum += trunc_x
        res.append(trunc_x)
    # now, if rounding errors did not add up to 0, fix this by randomly seeding the difference
    # and remembering the number of extra rolls (for statistics and a fun message to the user)
    if res_sum > n:
        # only select positive dice pool slots and maintain this condition
        indices = [x for x in range(0, k - 1) if res[x] > 0]
        for _ in range(res_sum - n):
            index = random.choice(indices)
            res[index] -= 1
            if res[index] <= 0: # can only subtract from positive numbers
                indices.remove(index)
    elif res_sum < n:
        # can add to any slot, a simpler algorithm
        for _ in range(n - res_sum):
            res[random.randint(0, k - 1)] += 1
    return {
        'results': res,
        'extra_dice': res_sum - n
    }

# Decides which approximation is better - normal or Poisson,
# and uses it to roll N dice with chance p of success for each die.
def roll_inverse(n, p):
    if p <= 0:
        return 0
    if p >= 1:
        return n
    if n * p <= 1.05: # benchmark results - de Moivre–Laplace catches up pretty fast
        return roll_inverse_poisson(n, p)
    return roll_inverse_normal(n, p)

def roll_normal(props):
    n = props['dicenum']
    k = props['dicetype']
    t = props['threshold']
    dc = props['dc']
    min = 1
    max = k
    isFate = str(props['dicetype'])[0] == 'F'
    if isFate:
        k = 3
        min = -1
        max = 1
    r = roll_inverse_normal_arr(n, k)
    scores = r['results']
    values = [1, 0, -1] if isFate else list(range(k, 0, -1)) # possible values of the dice
    dicearr = dice_str_array(values, min, max, isFate, t, False, False)
    dicezip = list(zip(dicearr, scores, values))
    dicestr = ', '.join([f'{z[0]}s: {z[1]}' for z in dicezip])
    if t is None:
        score = sum([z[2]*z[1] for z in dicezip])
    else:
        score = sum([z[1] for z in dicezip if z[2] >= t])
    description = None
    if isFate:
        description = get_fate_score(score)
    method_name = random.choice(['elliptical curves', 'Riemann space', 'Lee algebra',
        'black hole evaporation', 'quantum computing', 'M-theory', 'spacetime wrapping', 'forbidden dark magic'])
    title = f'{n} dice using {method_name}'
    if r['extra_dice']: # fun text
        extra = abs(r['extra_dice'])
        dice_text = 'die' if extra == 1 else 'dice'
        verb = 'gone into' if r['extra_dice'] > 0 else 'emerged from'
        portal_name = random.choice(['under event horizon', 'Taylor series expansion', 'a wormhole', 'quantum fluctuation',
            'a supersymmetry violation', 'a parallel universe', 'the Umbral world'])
        title += f', {extra} extra {dice_text} {verb} {portal_name}'
    return {
        'score': score,
        'str': dicestr,
        'success': result_success(score, dc),
        'overkill': result_overkill(score, dc),
        'title': title,
        'description': description
    }

def roll_threshold(props):
    n = props['dicenum']
    d = props['dicetype']
    t = props['threshold']
    dc = props['dc']
    success_sides = d - t + 1 # number of sides treated as success
    p = success_sides / d # chance of success on a single die
    r = roll_inverse(n, p) # number of direct successes in the roll
    b = 0 # botch dice number
    ex = 0 # exploded dice number
    method_name = random.choice(['an infinite hotel', 'Cantor\'s diagonal argument', 'quaternions',
        'Graham\'s number', 'Galois theory', 'condensed matter', 'superconductivity', 'witchcraft'])
    title = f'{n} dice using {method_name}'
    dicestr_success = f'{r}'
    dicestr_fail = f'{n - r}'
    dicestr_explode = ''
    dicestr_botch = ''
    if not props['nobotch']:
        # have to roll remaining dice for 1s
        unsuccess = n - r # number of remaining dice
        botch_chance = 1 if t == 0 else 1 / t # 1 among [1..t-1]
        b = roll_inverse(unsuccess, botch_chance)
        dicestr_botch = f' ({b} of them botched)'
    if props['explode']:
        # have to roll successfu dice for explosions
        expl_chance = 1 / (d - t + 1) # 1 last among [t..d]
        ex = roll_inverse(r, expl_chance)
        dicestr_explode = f' ({ex} of them exploded)'
    score = r - b + ex
    dicestr = f'Threshold: {t}\r\nSuccess: {dicestr_success} dice{dicestr_explode}\r\nFail: {dicestr_fail} dice{dicestr_botch}'
    return {
        'score': score,
        'str': dicestr,
        'success': result_success(score, dc),
        'overkill': result_overkill(score, dc),
        'title': title,
        'description': None
    }

# Rolls n d-sided dice for a total result, using the Central Limit Theorem
def roll_sum_central(n, d):
    min = n
    max = n * d
    average = n * (d + 1) / 2
    msd = math.sqrt(n)
    s = random.random()
    erfi = scipy.special.erfinv(2*s-1)
    sum = average + msd * erfi
    if sum < min:
        sum = min
    if sum > max:
        sum = max
    return math.trunc(sum + 0.5)

def roll_sum(props):
    # except for botches and explosions, this is a straightforward normally-distributed roll
    n = props['dicenum']
    d = props['dicetype']
    n_remaining = n # TODO: account for explosions and botches
    d_remaining = d
    shift = 0
    score = roll_sum_central(n, d)
    dicestr = '(calculating total...)'
    dc = props['dc']
    method_name = random.choice(['Goldbach\'s conjecture', 'Calabi-Yau manifolds', 'Fourier transform',
        'Conway arrow notation', 'fractal geometry', 'subatomic particles', 'Schrödinger\'s equation', 'demon summoning'])
    title = f'{n} dice using {method_name}'
    return {
        'score': score,
        'str': dicestr,
        'success': result_success(score, dc),
        'overkill': result_overkill(score, dc),
        'title': title,
        'description': None
    }

# Checks number of dice and number of sides, forks execution into
# the most appropriate method.
def roll_fork(props):
    if props['dicenum'] <= 100:
        return roll_straight(props) # few dice - roll directly each die
    if str(props['dicetype'])[0] == 'F' or props['dicetype'] <= 100:
        return roll_normal(props) # lots of dice, few faces each - can create an array res where res[k] = number of dice that landed on k
        # using only normal approximation here - it's out of range of Poisson feasibility
    # lots of dice AND lots of faces each - can only get approximate overall statistics
    if props['threshold'] is not None:
        return roll_threshold(props)
    return roll_sum(props)

def roll(props):
    res = roll_fork(props)
    if not res:
        return None
    res['unparse'] = unparse(props)
    res['unparse_full'] = unparse_full(props)
    return res

def roll_result_to_str(res):
    title = res['title']
    unparse = res['unparse_full']
    r = f'{title} ({unparse}):\r\n' if title else f'{unparse}:\r\n'
    r += res['str'] + '\r\n'
    score = res['score']
    success = res['success']
    overkill = res['overkill']
    description = res['description']
    if description:
        r += f'<b>{description}</b>'
    elif success:
        r += f'<b>Success</b>'
        if overkill is not None:
            r += f' by {overkill}'
    elif success is not None and score < 0:
        r += f'<b>Botch</b>'
        if overkill is not None:
            r += f' by {overkill}'
    elif success is not None:
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
# print(roll_code('1000000d1000t900!'))
# print('\r\n\r\nEnd debug session\r\n\r\n')
