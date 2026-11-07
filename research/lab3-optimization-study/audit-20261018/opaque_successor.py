"""Exact Python algorithm PoC, operation counts only; not a benchmark.

Each target row owns a successor DSU over pixels 0..W, including sentinel W.
Path compression plus union-by-size makes the complexity claim explicit.
Painting x merges x with x+1; the component maximum is its next unpainted
successor. Reverse command order preserves last opaque writer semantics.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import numpy as np

W, H = 1024, 600
HERE = Path(__file__).resolve().parent
COLORS = [0xffff0000, 0xffffa500, 0xffffff00, 0xff00ff00, 0xff007fff,
          0xff0000ff, 0xff8b00ff, 0xffffffff, 0xff000000]


class Successor:
    def __init__(self, width, stats):
        self.parent = list(range(width + 1))
        self.end = list(range(width + 1))
        self.size = [1] * (width + 1)
        self.stats = stats
        stats['initialized_nodes'] += width + 1

    def find(self, x):
        self.stats['find_calls'] += 1
        root = x
        while self.parent[root] != root:
            self.stats['find_parent_hops'] += 1
            root = self.parent[root]
        while x != root:
            next_x = self.parent[x]
            self.parent[x] = root
            self.stats['compression_assignments'] += 1
            x = next_x
        return root

    def successor(self, x):
        self.stats['successor_calls'] += 1
        return self.end[self.find(x)]

    def union(self, a, b):
        self.stats['union_calls'] += 1
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        # Union by size is essential: do not silently assume the representative
        # is the rightmost pixel. The separate end[] tracks that maximum.
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        self.end[a] = max(self.end[a], self.end[b])
        self.stats['successful_unions'] += 1


def line_points(x1, y1, x2, y2):
    """Same phase as geometry_v5.h; no closed-form floating approximation."""
    dx, dy = x2 - x1, y2 - y1
    steep = abs(dy) > abs(dx)
    major1, major2 = (y1, y2) if steep else (x1, x2)
    minor1, minor2 = (x1, x2) if steep else (y1, y2)
    if major1 > major2:
        major1, major2, minor1, minor2 = major2, major1, minor2, minor1
    length, distance = major2 - major1, abs(minor2 - minor1)
    step = -1 if minor2 < minor1 else 1
    error, minor = length // 2, minor1
    for major in range(major1, major2 + 1):
        yield (minor, major) if steep else (major, minor)
        error += distance
        if length and error >= length:
            error -= length
            minor += step


def closed_form_line_oracle(x1, y1, x2, y2):
    """Independent quotient formulation of the baseline raster phase."""
    steep = abs(y2-y1) > abs(x2-x1)
    m1,m2,n1,n2 = (y1,y2,x1,x2) if steep else (x1,x2,y1,y2)
    if m1>m2:m1,m2,n1,n2=m2,m1,n2,n1
    length,delta=m2-m1,abs(n2-n1)
    sign=-1 if n2<n1 else 1
    result=[]
    for major in range(m1,m2+1):
        minor=n1+sign*((delta*(major-m1)+length//2)//length if length else 0)
        result.append((minor,major) if steep else (major,minor))
    return result


def clipped_line_oracle(x1, y1, x2, y2, width=W, height=H):
    """Baseline quotient phase, clipped major range; bounded for huge endpoints."""
    steep=abs(y2-y1)>abs(x2-x1)
    m1,m2,n1,n2=(y1,y2,x1,x2) if steep else (x1,x2,y1,y2)
    if m1>m2:m1,m2,n1,n2=m2,m1,n2,n1
    length,delta=m2-m1,abs(n2-n1)
    sign=-1 if n2<n1 else 1
    limit=height if steep else width
    result=[]
    for major in range(max(0,m1),min(limit-1,m2)+1):
        minor=n1+sign*((delta*(major-m1)+length//2)//length if length else 0)
        x,y=(minor,major) if steep else (major,minor)
        if 0<=x<width and 0<=y<height:result.append((x,y))
    return result


def analytic_line_spans(x1,y1,x2,y2,color,stats=None,width=W,height=H):
    """Return exact (y,left,right,color) runs without enumerating line pixels.

    Python integers avoid overflow in endpoint differences and k*L. A C port
    needs a proved wide signed type (potentially __int128 for full int32 input).
    """
    if stats is None:stats=Counter()
    stats['input_lines']+=1
    steep=abs(y2-y1)>abs(x2-x1)
    m1,m2,n1,n2=(y1,y2,x1,x2) if steep else (x1,x2,y1,y2)
    if m1>m2:m1,m2,n1,n2=m2,m1,n2,n1
    length,distance=m2-m1,abs(n2-n1)
    sign=-1 if n2<n1 else 1
    spans=[]
    if steep:
        # Intersect BOTH coordinates before iterating: every remaining row
        # outputs exactly one valid span, so generation is O(N+K), not O(NH).
        qmin,qmax=max(0,-m1),min(length,height-1-m1)
        if distance==0:
            if not 0<=n1<width:return []
        else:
            if sign>0:kmin,kmax=max(0,-n1),min(distance,width-1-n1)
            else:kmin,kmax=max(0,n1-(width-1)),min(distance,n1)
            if kmin>kmax:return []
            if kmin>0:
                stats['integer_divisions']+=1
                qmin=max(qmin,-((-(kmin*length-length//2))//distance))
            if kmax<distance:
                stats['integer_divisions']+=1
                qmax=min(qmax,-((-((kmax+1)*length-length//2))//distance)-1)
        # The major coordinate is exactly destination y: one possible x each.
        for y in range(m1+qmin,m1+qmax+1):
            stats['target_row_evaluations']+=1
            x=n1
            if distance:
                stats['integer_divisions']+=1
                x+=sign*((distance*(y-m1)+length//2)//length)
            assert 0<=x<width and 0<=y<height
            spans.append((y,x,x+1,color))
    elif distance==0:
        stats['horizontal_or_point_lines']+=1
        if 0<=n1<height:
            stats['target_row_evaluations']+=1
            left,right=max(0,m1),min(width,m2+1)
            if left<right:spans.append((n1,left,right,color))
    else:
        bias=length//2
        qmin,qmax=max(0,-m1),min(length,width-1-m1)
        if qmin>qmax:return []
        # Shallow lines visit every minor value between these two endpoints.
        low_minor,high_minor=n1,n2
        if qmin:
            stats['integer_divisions']+=1
            low_minor=n1+sign*((distance*qmin+bias)//length)
        if qmax<length:
            stats['integer_divisions']+=1
            high_minor=n1+sign*((distance*qmax+bias)//length)
        # The raster quotient k is nonnegative even when the line descends.
        for y in range(max(0,min(low_minor,high_minor)),min(height-1,max(low_minor,high_minor))+1):
            stats['target_row_evaluations']+=1
            stats['integer_divisions']+=2
            k=(y-n1)*sign
            # ceil(a / b) == -((-a) // b), valid for negative a in Python.
            qlo=-((-(k*length-bias))//distance)
            qhi=-((-((k+1)*length-bias))//distance)-1
            qlo=max(qlo,qmin)
            qhi=min(qhi,qmax)
            assert qlo<=qhi
            spans.append((y,m1+qlo,m1+qhi+1,color))
    stats['output_spans']+=len(spans)
    return spans


def append_span(rows, x, y, length, color):
    if not 0 <= y < H:
        return
    left, right = max(0, x), min(W, x + length)
    if left < right:
        rows[y].append((left, right, color))


def course_rectangles():
    commands = []
    color = 0
    for y in range(-15, 300, 5):
        for x in range(-15, 1029, 5):
            commands.append((x, y, 10, 10, COLORS[color]))
            color = (color + 1) % 9
    color = 0
    for y in range(300, 605, 5):
        commands.append((0, y, 500, 10, COLORS[color]))
        color = (color + 1) % 9
    color = 0
    for x in range(500, 1029, 5):
        commands.append((x, 300, 10, 300, COLORS[color]))
        color = (color + 1) % 9
    return commands


def rectangle_inputs(background):
    reference = background.copy()
    rows = [[] for _ in range(H)]
    visits = np.zeros((H, W), np.uint32)
    commands = course_rectangles()
    visible = 0
    for x, y, width, height, color in commands:
        left, right = max(x, 0), min(x + width, W)
        top, bottom = max(y, 0), min(y + height, H)
        if left >= right or top >= bottom:
            continue
        visible += 1
        reference[top:bottom, left:right] = color
        visits[top:bottom, left:right] += 1
        for row in range(top, bottom):
            append_span(rows, left, row, right - left, color)
    return reference, rows, visits, dict(input_commands=len(commands),
                                         visible_commands=visible,
                                         point_generation_steps=0)


def line_inputs(background):
    reference = background.copy()
    rows = [[] for _ in range(H)]
    visits = np.zeros((H, W), np.uint32)
    commands = [(200, 100 + i, 800, 500 - i, COLORS[1]) for i in range(401)]
    commands += [(300 + i, 100, 700 - i, 500, COLORS[2]) for i in range(401)]
    steps = 0
    for x1, y1, x2, y2, color in commands:
        point_rows = {}
        points=list(line_points(x1,y1,x2,y2))
        assert points==closed_form_line_oracle(x1,y1,x2,y2)
        for x, y in points:
            steps += 1
            if 0 <= x < W and 0 <= y < H:
                reference[y, x] = color
                visits[y, x] += 1
                point_rows.setdefault(y, []).append(x)
        # A monotone Bresenham line's same-row x values form a consecutive run.
        # Assert rather than assume; retain one row-span per consecutive run.
        for y, xs in point_rows.items():
            xs.sort()
            start = previous = xs[0]
            for x in xs[1:]:
                if x != previous + 1:
                    append_span(rows, start, y, previous - start + 1, color)
                    start = x
                previous = x
            append_span(rows, start, y, previous - start + 1, color)
    return reference, rows, visits, dict(input_commands=len(commands),
                                         visible_commands=len(commands),
                                         closed_form_raster_phase_checks=len(commands),
                                         point_generation_steps=steps)


def analytic_line_inputs(background):
    reference,enumerated_rows,visits,info=line_inputs(background)
    commands=[(200,100+i,800,500-i,COLORS[1]) for i in range(401)]
    commands += [(300+i,100,700-i,500,COLORS[2]) for i in range(401)]
    rows=[[] for _ in range(H)]
    generation=Counter()
    for x1,y1,x2,y2,color in commands:
        for y,left,right,ink in analytic_line_spans(x1,y1,x2,y2,color,generation):
            rows[y].append((left,right,ink))
    assert rows==enumerated_rows
    info['enumeration_is_reference_only']=True
    info['candidate_point_generation_steps']=0
    info['analytic_generation']=dict(generation)
    return reference,rows,visits,info


def test_analytic_line_spans():
    rng=np.random.default_rng(81230)
    tests=[]
    # All octants, exact half-step cases, horizontal/vertical, points, reverse.
    for dx in (-61,-31,-17,-8,-3,-1,0,1,3,8,17,31,61):
        for dy in (-61,-31,-17,-8,-3,-1,0,1,3,8,17,31,61):
            for origin in ((0,0),(31,23),(-9,-7),(64,48)):
                a=(*origin,origin[0]+dx,origin[1]+dy)
                tests.append(a)
                tests.append((a[2],a[3],a[0],a[1]))
    for _ in range(3000):
        a=tuple(int(x) for x in rng.integers(-130,195,4))
        tests.append(a)
        tests.append((a[2],a[3],a[0],a[1]))
    extremes=[(-(2**31),-(2**31),2**31-1,2**31-1),
              (-(2**31),2**31-1,2**31-1,-(2**31)),
              (-(2**31),17,2**31-1,18),(17,-(2**31),18,2**31-1),
              (2**31-1,22,2**31-1,22),(-(2**31),-1,2**31-1,-1)]
    tests.extend(extremes)
    tests.extend((a[2],a[3],a[0],a[1]) for a in extremes)
    visible_pixels=0
    for a in tests:
        reference=set(clipped_line_oracle(*a,width=64,height=48))
        spans=analytic_line_spans(*a,color=7,width=64,height=48)
        actual={(x,y) for y,left,right,_ in spans for x in range(left,right)}
        assert actual==reference,(a,sorted(actual^reference))
        assert all(0<=left<right<=64 and 0<=y<48 for y,left,right,_ in spans)
        visible_pixels+=len(actual)
    return dict(cases=len(tests),compared_visible_pixels=visible_pixels,
                dimensions=[64,48],all_equal=True,
                included='eight octants, reverse endpoints, clipping, horizontal/vertical/point, signed int32 extremes')


def reverse_successor(background, rows):
    rendered = background.copy()
    stats = Counter()
    for y, spans in enumerate(rows):
        dsu = Successor(W, stats)
        for left, right, color in reversed(spans):
            stats['input_spans'] += 1
            x = dsu.successor(left)
            while x < right:
                assert 0 <= x < W
                rendered[y, x] = color
                stats['unique_pixel_writes'] += 1
                dsu.union(x, x + 1)
                x = dsu.successor(x)
    return rendered, dict(stats)


def edge_cases():
    """Exercise sentinel, reverse order, disjoint spans, and rank direction."""
    rng = np.random.default_rng(127)
    checks = 0
    for width in (1, 2, 3, 9, 31):
        for _ in range(20):
            rows = [(int(rng.integers(0, width)), int(rng.integers(1, width + 1)),
                     int(rng.integers(0, 256))) for _ in range(40)]
            rows = [(min(l, r - 1), max(l + 1, r), c) for l, r, c in rows]
            direct = np.arange(width, dtype=np.uint32)
            rev = direct.copy()
            for left, right, color in rows:
                direct[left:right] = color
            stats = Counter()
            dsu = Successor(width, stats)
            for left, right, color in reversed(rows):
                x = dsu.successor(left)
                while x < right:
                    rev[x] = color
                    dsu.union(x, x + 1)
                    x = dsu.successor(x)
            assert np.array_equal(direct, rev)
            assert dsu.successor(width) == width
            checks += 1
    return checks


def main():
    rng = np.random.default_rng(20261018)
    background = rng.integers(0, 2**32, (H, W), dtype=np.uint32)
    results = dict(measurement_type='Python correctness PoC and operation counts; not timed',
                   framebuffer=[W, H],dsu='union-by-size + path compression + component maximum end',
                   extra_edge_cases=edge_cases(),analytic_line_cases=test_analytic_line_spans(),workloads={})
    for name, prepare in [('course_rectangles', rectangle_inputs), ('course_lines', line_inputs),
                          ('course_lines_analytic',analytic_line_inputs)]:
        reference, rows, visits, info = prepare(background)
        rendered, stats = reverse_successor(background, rows)
        assert np.array_equal(reference, rendered)
        assert stats['unique_pixel_writes'] == int((visits > 0).sum())
        assert sum(right-left for row in rows for left,right,_ in row) == int(visits.sum())
        assert stats['successful_unions'] == stats['unique_pixel_writes']
        assert stats['union_calls'] == stats['unique_pixel_writes']
        assert stats['successor_calls'] == stats['input_spans'] + stats['unique_pixel_writes']
        assert stats['find_calls'] == stats['input_spans'] + 3 * stats['unique_pixel_writes']
        info.update(original_pixel_writes=int(visits.sum()),
                    unique_pixels=int((visits > 0).sum()),
                    equal_32bit_pixels=W*H,
                    both_sha256=hashlib.sha256(rendered.tobytes()).hexdigest(),
                    stats=stats)
        results['workloads'][name] = info
    results['complexity'] = {
        'span_stage': 'O(HW + N + K + (K+U)*alpha(W)), memory O(H+K+W) excluding output frame',
        'enumerated_line_generation': 'The retained enumerated comparison version costs O(L), where L=sum major-axis lengths+1.',
        'analytic_line_generation': 'O(N+K) generation after exact clipping of BOTH major and minor ranges; every iterated row yields a valid span. Combine with DSU: O(HW+N+K+(K+U)*alpha(W)).',
        'rect_generation': 'O(N+K), where K=sum clipped row spans.',
        'warning': 'DSU reduces writes, not necessarily runtime; Python counts are not ARM performance.'}
    (HERE/'opaque-successor-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
