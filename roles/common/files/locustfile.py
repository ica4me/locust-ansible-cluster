from __future__ import annotations
from locust import FastHttpUser, task

class SingleEndpointUser(FastHttpUser):
    # Host didefinisikan langsung atau melalui parameter --host saat runtime
    host = "http://fasthttp.poc.dcloud.biz.id:8080"
    
    # Connection dan network timeout diperkecil agar tidak menumpuk saat server mulai lambat
    connection_timeout = 5.0
    network_timeout = 10.0

    # wait_time DIHAPUS agar user melakukan request secepat mungkin secara konstan (banjir traffic)

    @task
    def hit_root(self) -> None:
        # Hanya melakukan GET ke endpoint /
        with self.client.get(
            "/",
            name="GET /",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed: HTTP {response.status_code}")
