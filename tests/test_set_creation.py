import dcs.core as core
import datetime as dt

data = core.read_coord_sink("tests/tacview_sink.json")
t1 = dt.datetime.now()
results = core.construct_enemy_set(data, result_as_string=False)



coord_fmt = 'dms'
enemy_state = core.read_coord_sink()
t1 = dt.datetime.now()
last_recv = enemy_state.pop('last_recv')
start_coord = None
start_pilot = 'None'
for pilot in ["someone_somewhere", "CVN-74", "Stennis"]:
    if start_coord:
        break
    for id, ent in enemy_state.items():
        if ent["Pilot"] == pilot or ent['Group'] == pilot:
            start_coord = (ent['LatLongAlt']['Lat'],
                           ent['LatLongAlt']['Long'])
            start_pilot = pilot
            break
enemy_groups = core.create_enemy_groups(enemy_state, start_coord,
                                        coord_fmt=coord_fmt)
t2 = dt.datetime.now()
print((t2-t1).total_seconds())





t1 = dt.datetime.now()
enemy_groups.sort()
with open(core.LAST_RUN_CACHE, 'w') as fp_:
    fp_.write(enemy_groups.serialize())
if True:
    results = {}
    for grp_name, enemy_set, grp_dist in enemy_groups:
        if start_coord and (grp_dist > MAX_DIST):
            log.info("Excluding %s...distance is %d...", grp_name,
                     grp_dist)
            continue
        grp_val = [e.str() for e in enemy_set]
        grp_val.insert(0, f"{grp_name}")
        results[grp_dist] = '\r\n\t'.join(grp_val)

    results = [results[k] for k in sorted(results.keys())]
    results = [f"{i+1}) {r}" for i, r in enumerate(results)]
    results = '\r\n\r\n'.join(results)
    results = f"Start Ref: {start_pilot} "\
              f"{(round(start_coord[0], 3), round(start_coord[1], 3))}"\
              f" {last_recv}\r\n\r\n{results}"
    results.encode('UTF-8')
t2 = dt.datetime.now()
print((t2-t1).total_seconds())
