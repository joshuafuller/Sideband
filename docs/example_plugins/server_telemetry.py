# This is a basic server telemetry plugin
# example that you can build upon to
# implement your own telemetry plugins.

import RNS
import time
import psutil
import shutil
from threading import Thread
import urllib.request, json

class ServerTelemetryPlugin(SidebandTelemetryPlugin):
    plugin_name = "server_telemetry"

    def start(self):
        # Do any initialisation work here
        RNS.log("Server Telemetry plugin starting...")
        self.initialise_values()
        
        self.power_stats   = False
        self.storage_stats = True
        self.target_disk   = {"blkid": "mmcblk0p2", "label": "SD Card"}
        self.should_run    = True
        
        self.update_thread = Thread(target=self.update_job, daemon=True)
        self.update_thread.start()

        # And finally call start on superclass
        super().start()

    def stop(self):
        # Do any teardown work here
        self.should_run = False

        # And finally call stop on superclass
        super().stop()

    def initialise_values(self):
        self.battery_percent = None
        self.power_production = None
        self.power_consumption = None
        self.battery_charging = None
        self.battery_temperature = None
        self.uptime = None

    def update_job(self):
        while self.should_run:
            try:
                # Update uptime
                self.uptime = RNS.prettytime(time.time()-psutil.boot_time())

                # Update power values if enabled
                if self.power_stats:
                    with urllib.request.urlopen("http://some_host/status.json") as url:
                        data = json.loads(url.read().decode())
                        self.power_production    = data["solar_yield"]
                        self.power_consumption   = data["inverter_load"]+data["dc_consumption"]
                        self.battery_charging    = data["battery_current"] >= 0.0
                        self.battery_charge      = data["battery_charge"]
                        self.battery_temperature = data["battery_temperature"]

            except Exception as e:
                RNS.log("Error while updating plugin telemetry: "+str(e), RNS.LOG_ERROR)

            time.sleep(15)

    def update_telemetry(self, telemeter):
        if telemeter != None:

            if self.power_stats:
                # Create power consumption sensor
                telemeter.synthesize("power_consumption")
                telemeter.sensors["power_consumption"].update_consumer(self.power_consumption, type_label="Power consumption")

                # Create power production sensor
                telemeter.synthesize("power_production")
                telemeter.sensors["power_production"].update_producer(self.power_production, type_label="Solar production", custom_icon="solar-power-variant")

                # Create battery sensor
                telemeter.synthesize("battery")
                telemeter.sensors["battery"].data = {"charge_percent": round(self.battery_charge, 1), "charging": self.battery_charging}

            
            # Create NVM sensor if enabled
            if self.storage_stats:
                mount_point = None
                for partition in psutil.disk_partitions(all=False):
                    if self.target_disk["blkid"] in partition.device:
                        mount_point = partition.mountpoint
                        break
                
                if mount_point:
                    st = shutil.disk_usage(mount_point)
                    telemeter.synthesize("nvm")
                    telemeter.sensors["nvm"].update_entry(capacity=st.total, used=st.used, type_label=self.target_disk["label"])

            # Create RAM sensors
            ms = psutil.virtual_memory()
            telemeter.synthesize("ram")
            telemeter.sensors["ram"].update_entry(capacity=ms.total, used=ms.used, type_label="RAM")

            # Create CPU sensor
            a = psutil.getloadavg()
            cps = 0; cpms = 5
            for m in range(cpms):
                cps += psutil.cpu_percent()/100.0
                time.sleep(0.05)
            cp = cps/cpms

            telemeter.synthesize("processor")
            telemeter.sensors["processor"].update_entry(current_load=cp, clock=round(psutil.cpu_freq().current*1e6, 0), load_avgs=[a[0], a[1], a[2]], type_label="CPU")

            # Create custom sensor for uptime
            telemeter.synthesize("custom")
            telemeter.sensors["custom"].update_entry(self.uptime, type_label="Uptime is", custom_icon="timer-refresh-outline")

# Finally, tell Sideband what class in this
# file is the actual plugin class.
plugin_class = ServerTelemetryPlugin