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
-------------------------------------------------------------------------------
10 last events:
{5}
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

last_events = 'Date & time      | Code | Source\n'
event_idx = b'FFFFFF'
for idx in range(10):
    res = integra.get_event(event_idx)
    last_events += (
        '{0.year:02d}-{0.month:02d}-{0.day:02d} '
        '{0.time} |  {0.code} | {0.source_number}\n'
    ).format(res)
    event_idx = res.event_index


print(
    template.format(
        integra.get_version(),
        integra.get_time(),
        armed_partitions,
        violated_zones,
        active_outputs,
        last_events
    )
)
