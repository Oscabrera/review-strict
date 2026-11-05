#!/usr/bin/env python3
"""Execute the repository's trusted synthetic examples; never live service inputs."""
import json
import os
from pathlib import Path

cases = json.loads(Path(__file__).with_name('review-lessons-cases.json').read_text())['cases']
results = []
for c in cases:
    ns = {}; exec(compile(c['source'], 'synthetic-case-'+c['id'], 'exec'), ns)
    id = c['id']
    if id == '01':
        paths = []
        previous = os.environ.get('SOURCE')
        try:
            for flag in ('legacy','service-b'):
                os.environ['SOURCE'] = flag
                ns['request'](lambda p: paths.append(p))
            try:
                def fail(path):
                    paths.append(path)
                    raise RuntimeError('synthetic transport failure')
                ns['request'](fail)
            except RuntimeError:
                pass
        finally:
            if previous is None: os.environ.pop('SOURCE',None)
            else: os.environ['SOURCE'] = previous
        observed = {'paths_for_both_flags_and_failure':paths}
    elif id in ('02','03'):
        observed = {'unknown_status':ns['validate'](None)}
        if id == '02':ns['test_unknown']()
        else:
            try: ns['request'](lambda path: (_ for _ in ()).throw(RuntimeError('sentinel')))
            except RuntimeError: observed['transport_error_propagated'] = True
    elif id == '04':
        initial=ns['preview']('same-basket',0,lambda:150)
        after_recovery=ns['preview']('same-basket',1,lambda:210)
        after_expiry=ns['preview']('same-basket',601,lambda:210)
        observed={'initial_degraded':initial,'after_recovery':after_recovery,'after_expiry':after_expiry}
    elif id in ('05','06'):
        for t in (0,10,20,30,40):
            ns['fail']('shared-host',t)
            if t<40:ns['success']('shared-host',t+1)
        observed={'same_host_endpoint_b_at_41':ns['blocked']('shared-host',41),'other_host_at_41':ns['blocked']('other-host',41),'at_70':ns['blocked']('shared-host',70)}
    elif id in ('07','08'):
        observed={'old_consumer':ns['consumed'](ns['old']),'new_consumer':ns['consumed'](ns['new'])}
    elif id == '09':
        observed={'old_consumer':ns['old_consumer'](ns['old']),'new_consumer':ns['new_consumer'](ns['new'])}
    else:
        observed={'route_only_result':ns['request'](lambda path:{})}
    results.append({'id':id,'observed':observed})
print(json.dumps(results,indent=2))
