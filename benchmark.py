import numpy
import scipy
import math
import matplotlib.pyplot as plt
import scipy.special

def binomial(n, p):
    t = 0
    r = []
    for m in range(n):
        t += scipy.special.comb(n, m) * math.pow(p, m) * math.pow(1-p, n-m)
        r.append(t)
    return r

def normal(n, p):
    np = n * p
    s2npqinv = 1 / math.sqrt(2*np*(1-p))
    r = []
    for m in range(n):
        er = scipy.special.erf((m-np)*s2npqinv)
        normal = (1+er)/2
        r.append(normal)
    return r

def poisson(n, p):
    t = 0
    r = []
    lmbd = n*p
    lmbd_m = 1
    e_minlmbd = math.exp(-lmbd)
    factinv = 1
    for m in range(10):
        t += lmbd_m * e_minlmbd * factinv
        lmbd_m *= lmbd
        factinv /= m + 1
        r.append(t)
    return r

def test(n, p):
    distr_b = binomial(n, p)
    distr_n = normal(n, p)
    distr_p = poisson(n, p)
    print(distr_p[-1])
    return
    for index in range(n):
        norm_error = abs(distr_n[index] - distr_b[index])
        pois_error = abs(distr_p[index] - distr_b[index])
        if norm_error < pois_error:
            print(index)
            break
    else:
        print('No index found')
    #x = list(range(n))
    #plt.plot(x, distr_b)
    #plt.plot(x, distr_n)
    #plt.plot(x, distr_p)
    #plt.show()

test(2000, 1.07/2000)