# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys

from .constants import PARTITION, ZONE, OUTPUT
from . import Integra

template = '''\
Model:            {0[model]}
Version:          {0[version]}
Time:             {1}
Armed partitions: {2}
Violated zones:   {3}
Active outputs:   {4}
'''

if len(sys.argv) < 2:
    print("demo <IP_ADDRESS_OF_THE_ETHM1_MODULE>", file=sys.stderr)
    sys.exit(1)

integra = Integra(user_code=1234, host=sys.argv[1])
armed_partitions = ', '.join(
    integra.get_name(PARTITION, part)
    for part in integra.get_armed_partitions()
)
violated_zones = ', '.join(
    integra.get_name(ZONE, zone).name
    for zone in integra.get_violated_zones()
)
active_outputs = ', '.join(
    integra.get_name(OUTPUT, out).name
    for out in integra.get_active_outputs()
)


print(
    template.format(
        integra.get_version(),
        integra.get_time(),
        armed_partitions,
        violated_zones,
        active_outputs
    )
)
