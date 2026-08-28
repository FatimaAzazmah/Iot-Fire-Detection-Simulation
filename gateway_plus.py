# gateway_plus.py
import socket, json, time, random, signal

HEARTBEAT_INTERVAL = 15
DATA_INTERVAL = 1
HOST, PORT = "localhost", 5555
BUF = 8192

class Gateway:
    def __init__(self, gw_id="GW-1", host=HOST, port=PORT):
        self.gw_id = gw_id
        self.host, self.port = host, port
        self.s = None
        self.connected = False
        self.seq = 0
        self.last_hb = 0
        self.paused = False

        # Two rooms + two cars
        self.room1 = {"smoke": 45.0, "co2": 850.0, "fire": 35.0}
        self.room2 = {"smoke": 42.0, "co2": 780.0, "fire": 32.0}
        self.car1 = {"status": "PARKED", "temp": 25.0}
        self.car2 = {"status": "PARKED", "temp": 25.0}

        # Scenario
        self.scenario = None
        self.sc_params = {}

        signal.signal(signal.SIGINT, self._sig)

    # --------- Connection ---------
    def connect(self):
        while True:
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((self.host, self.port))
                self.s.setblocking(False)
                self.connected = True
                print("[GW] Connected to cloud")
                self._heartbeat()
                break
            except Exception as e:
                print("[GW] connect error:", e)
                time.sleep(2)

    def _send(self, obj):
        if not self.connected: return False
        try:
            self.s.sendall((json.dumps(obj)+"\n").encode())
            return True
        except Exception:
            self.connected = False
            try: self.s.close()
            except: pass
            return False

    # --------- Messages ---------
    def _heartbeat(self):
        self.seq += 1
        self._send({"type":"HEARTBEAT","gateway_id":self.gw_id,"seq":self.seq,"timestamp":time.time()})
        self.last_hb = time.time()

    def _send_data(self):
        self.seq += 1
        msg = {
            "type":"DATA",
            "gateway_id": self.gw_id,
            "seq": self.seq,
            "timestamp": time.time(),
            "sensors": {
                # Room 1200400
                "smoke1": round(self.room1["smoke"],2),
                "co2_1":  round(self.room1["co2"],0),
                "fire1":  round(self.room1["fire"],2),
                # Room 1211371
                "smoke2": round(self.room2["smoke"],2),
                "co2_2":  round(self.room2["co2"],0),
                "fire2":  round(self.room2["fire"],2),
                # Car 1
                "car1_temp": round(self.car1["temp"],1),
                "car1_status": self.car1["status"],
                # Car 2
                "car2_temp": round(self.car2["temp"],1),
                "car2_status": self.car2["status"]
            }
        }
        self._send(msg)

    # --------- Value generation ---------
    def _tick(self):
        # Natural noise for the rooms
        for r in (self.room1, self.room2):
            r["smoke"] = max(0.0, min(100.0, r["smoke"] + random.uniform(-0.5,0.7)))
            r["co2"]   = max(350.0, min(3000.0, r["co2"]   + random.uniform(-5,8)))
            r["fire"]  = max(20.0, min(120.0, r["fire"]  + random.uniform(-0.3,0.5)))

        # Car temperature based on status
        for car in (self.car1, self.car2):
            if car["status"] in ("RUNNING","IDLING"):
                car["temp"] = min(130.0, car["temp"] + random.uniform(0.4,1.4))
            else:
                car["temp"] = max(20.0, car["temp"] - random.uniform(0.2,0.5))

        # Scenario effects
        if self.scenario == "fire1":
            self.room1["smoke"] += 0.9
            self.room1["co2"]   += 15
            self.room1["fire"]  += 0.7
        elif self.scenario == "fire2":
            self.room2["smoke"] += 0.9
            self.room2["co2"]   += 15
            self.room2["fire"]  += 0.7
        elif self.scenario == "co2_high":
            room = (self.sc_params.get("room") or "1200400")
            target = self.room1 if room == "1200400" else self.room2
            target["co2"] += 25  # Raise CO2 only
        elif self.scenario == "car1":
            self.car1["status"] = "RUNNING"
            self.car1["temp"]   = max(self.car1["temp"], 35)
        elif self.scenario == "car2":
            self.car2["status"] = "RUNNING"
            self.car2["temp"]   = max(self.car2["temp"], 35)

    # --------- Control from the cloud ---------
    def _handle_control(self, msg):
        cmd = msg.get("command","").upper()
        params = msg.get("params",{}) or {}
        if cmd == "PAUSE":
            self.paused = True
            print("[GW] ▶ paused")
        elif cmd == "RESUME":
            self.paused = False
            print("[GW] ▶ resumed")
        elif cmd == "SCENARIO":
            name = (params.get("name") or "").lower()
            self.sc_params = params
            if name in ("fire1","fire2","co2_high","car1","car2"):
                self.scenario = name
                print(f"[GW] scenario -> {name} params={params}")
            elif name == "normal":
                self.scenario = None
                self.room1.update({"smoke":45.0,"co2":850.0,"fire":35.0})
                self.room2.update({"smoke":42.0,"co2":780.0,"fire":32.0})
                self.car1.update({"status":"PARKED","temp":25.0})
                self.car2.update({"status":"PARKED","temp":25.0})
                print("[GW] ↩ normal")

    def _recv_loop(self):
        try:
            data = self.s.recv(BUF)
            if not data: 
                self.connected = False
                return
            for line in data.decode().splitlines():
                if not line.strip(): continue
                try:
                    msg = json.loads(line)
                    if msg.get("type") == "CONTROL":
                        self._handle_control(msg)
                except: 
                    pass
        except BlockingIOError:
            pass

    # --------- Run loop ---------
    def run(self):
        self.connect()
        t0 = 0
        while True:
            if not self.connected:
                print("[GW] reconnecting ...")
                time.sleep(1)
                self.connect()

            now = time.time()
            if now - self.last_hb >= HEARTBEAT_INTERVAL:
                self._heartbeat()

            if not self.paused and now - t0 >= DATA_INTERVAL:
                self._tick()
                self._send_data()
                t0 = now

            self._recv_loop()
            time.sleep(0.05)

    def _sig(self, *a):
        try:
            if self.s: self.s.close()
        finally:
            raise SystemExit

if __name__ == "__main__":
    Gateway().run()
