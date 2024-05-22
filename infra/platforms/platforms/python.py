from subprocess import Popen, PIPE
from typing import Optional, List
from pathlib import Path
import os
import re

from .fpcore import FPCore
from .runner import Runner
from .util import double_to_c_str

# Supported operations for Python
unary_ops = ['neg', 'acos', 'acosh', 'asin', 'asinh', 'atan', 'atanh', 'ceil', 'cos', 'cosh', 'erf', 'erfc', 'exp', 'expm1', 'fabs', 'floor', 'lgamma', 'log', 'log10', 'log2', 'log1p', 'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'tgamma', 'trunc']
binary_ops = ['+', '-', '*', '/', 'atan2', 'copysign', 'fmax', 'fmin', 'fmod', 'hypot', 'pow', 'remainder']
ternary_ops = []
nary_ops = [(3, 'sum3'), (4, 'sum4')]

# Pyton lang
target = 'python3'
driver_name = 'main.py'
time_unit = 'ms'

# Regex patterns
time_pat = re.compile(f'([-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)(e[-+]?[0-9]+)?) {time_unit}')

class PythonRunner(Runner):
    """`Runner` for Python 3.10"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name='python',
            lang='python',
            unary_ops=unary_ops,
            binary_ops=binary_ops,
            ternary_ops=ternary_ops,
            nary_ops=nary_ops,
            time_unit='ms',
            **kwargs
        )

    def make_drivers(self, cores: List[FPCore], driver_dirs: List[str], samples: dict) -> None:
        for core, driver_dir in zip(cores, driver_dirs):
            driver_path = os.path.join(driver_dir, driver_name)
            _, sample = self.cache.get_core(core.key)
            input_points, _ = sample
            with open(driver_path, 'w') as f:
                print('import math', file=f)
                print('import time', file=f)
                print(f'{core.compiled}', file=f)

                spoints = []
                for i, points in enumerate(input_points):
                    for pt in points:
                        s = double_to_c_str(pt)
                        if s == 'NAN':
                            spoints.append('math.nan')
                        else:
                            spoints.append(s)

                    print(f'x{i} = [', file=f)
                    print(',\n'.join(spoints), file=f)
                    print(']', file=f)

                arg_str = ', '.join(map(lambda i: f'x{i}[j]', range(core.argc)))
                print('if __name__ == "__main__":', file=f)
                print(f'\ti = 0', file=f)
                print(f'\tstart = time.time_ns()', file=f)
                print(f'\twhile i < {self.num_inputs}:', file=f)
                print(f'\t\ttry:', file=f)
                print(f'\t\t\tfor j in range(i, {self.num_inputs}):', file=f)
                print(f'\t\t\t\tfoo({arg_str})', file=f)
                print(f'\t\t\t\ti += 1', file=f)
                print(f'\t\texcept:', file=f)
                print(f'\t\t\ti += 1', file=f)
                print(f'\tend = time.time_ns()', file=f)
                print(f'\tdiff = (10 ** -6) * (end - start)', file=f)
                print(f'\tprint(f\'{{diff}} ms\')', file=f)

        self.log(f'created drivers')
    
    def compile_drivers(self, driver_dirs: List[str]) -> None:
        self.log(f'drivers interpreted, skipping compilations')

    def run_drivers(self, driver_dirs: List[str]) -> List[float]:
        # run processes sequentially
        times = [[] for _ in driver_dirs]
        for i, driver_dir in enumerate(driver_dirs):
            log_prefix = f'[{i}/{len(driver_dirs)}] '
            print(log_prefix, end='', flush=True)
            for _ in range(self.num_runs):
                driver_path = Path(os.path.join(driver_dir, driver_name))
                p = Popen([target, driver_path], stdout=PIPE)
                stdout, _ = p.communicate()
                output = stdout.decode('utf-8')
                time = re.match(time_pat, output)
                if time is None:
                    raise RuntimeError('Unexpected error when running {out_path}: {output}')
                times[i].append(float(time.group(1)))
                print('.', end='', flush=True)

            # Reset terminal
            print('\r', end='', flush=True)
            print(' ' * (len(log_prefix) + self.num_runs), end='', flush=True)
            print('\r', end='', flush=True)
            
        print()
        
        times = [sum(ts) / len(ts) for ts in times]
        self.log(f'run drivers')
        return times
