def kmh_to_ms(v_list):
    return [v / 3.6 for v in v_list]

def calculate_rectangle(v_ms, h):
    return h * sum(v_ms[:-1])

def calculate_trapezoidal(v_ms, h):
    n = len(v_ms)
    # Formula: (h/2) * (y0 + 2*y1 + 2*y2 + ... + yn)
    inner_sum = sum(v_ms[1:-1])
    return (h / 2) * (v_ms[0] + 2 * inner_sum + v_ms[-1])

def calculate_simpson(v_ms, h):
    n_points = len(v_ms)
    n_intervals = n_points - 1
    
    # Simpson's rule requires an even number of intervals (odd number of points). If we have an odd number of intervals, we can apply Simpson's rule to the first n-1 intervals and use the trapezoidal rule for the last interval. 
    # This way we can handle any number of points without losing accuracy on the majority of the data.
    if n_intervals % 2 != 0:
        # Simpson's rule on the first n-1 points (even number of intervals)
        v_simpson = v_ms[:-1]
        dist_simpson = (h / 3) * (
            v_simpson[0] + 
            4 * sum(v_simpson[1:-1:2]) + 
            2 * sum(v_simpson[2:-2:2]) + 
            v_simpson[-1]
        )
        # Trapezoidal rule on the last interval (points n-2 and n-1)
        dist_last = (h / 2) * (v_ms[-2] + v_ms[-1])
        return dist_simpson + dist_last
    else:
        # Simpson standard
        return (h / 3) * (
            v_ms[0] + 
            4 * sum(v_ms[1:-1:2]) + 
            2 * sum(v_ms[2:-1:2]) + 
            v_ms[-1]
        )