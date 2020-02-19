#!/usr/bin/env python
# import yappi
from dcs import tacview

# filename = 'callgrind.tacview.prof'
# yappi.set_clock_type('cpu')
# yappi.start(builtins=True)

tacview.client.main(host='127.0.0.1',
                    port=5555,
                    debug=False,
                    max_iters=50000,
                    only_proc=False)

# stats = yappi.get_func_stats()
# stats.save(filename, type='callgrind')
# stats.print_all()
