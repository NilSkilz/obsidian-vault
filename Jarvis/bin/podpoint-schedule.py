#!/home/jarvis/.venvs/podpoint/bin/python
"""Pod Point charge schedule tool (Octopus Go window lives ON the charger, not in HA).

  podpoint-schedule.py show
  podpoint-schedule.py set 00:30 05:30     # daily window, smart mode on
  podpoint-schedule.py clear               # no schedule, manual mode (charge any time)

HA's "Charging Allowed" switch overwrites this with an all-or-nothing schedule,
so don't use it; use the charge_now service to boost instead.
Creds: ~/.config/jarvis/podpoint.env
"""
import asyncio
import os
import sys

import aiohttp


def load_env():
    path = os.path.expanduser("~/.config/jarvis/podpoint.env")
    env = {}
    for line in open(path):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v.strip().strip('"').strip("'")
    return env


def describe(pod):
    print(f"pod {pod.ppid} unit {pod.unit_id} mode {pod.charge_mode}")
    for s in pod.charge_schedules or []:
        print(f"  day {s.start_day} {s.start_time} -> day {s.end_day} {s.end_time} active={s.is_active}")


async def main(argv):
    # imported here: podpointclient builds a ClientSession at import time, which needs a running loop
    from podpointclient.client import PodPointClient
    from podpointclient.factories import ScheduleFactory
    from podpointclient.helpers.functions import auth_headers

    env = load_env()
    async with aiohttp.ClientSession() as session:
        client = PodPointClient(username=env["PODPOINT_EMAIL"], password=env["PODPOINT_PASSWORD"], session=session)
        pods = await client.async_get_all_pods()
        pod = pods[0]
        cmd = argv[0] if argv else "show"

        if cmd == "set":
            await client.auth.async_update_access_token()
            start, end = (t if t.count(":") == 2 else t + ":00" for t in argv[1:3])
            schedules = ScheduleFactory().build_schedules(enabled=True, start_time=start, end_time=end)
            resp = await client.api_wrapper.put(
                url=client._url_from_path(path=f"/units/{pod.unit_id}/charge-schedules"),
                params=client._generate_complete_params(params=None),
                headers=auth_headers(access_token=client.auth.access_token),
                body={"data": [s.dict for s in schedules]},
            )
            print("schedule PUT", resp.status, "" if resp.status == 201 else await resp.text())
            await client.async_set_charge_mode_smart(pod)
        elif cmd == "clear":
            await client.async_set_schedule(enabled=False, pod=pod)
            await client.async_set_charge_mode_manual(pod)

        pod = (await client.async_get_all_pods())[0]
        describe(pod)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
