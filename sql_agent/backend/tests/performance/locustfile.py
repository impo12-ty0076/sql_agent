"""
Load testing script using Locust for the SQL DB LLM Agent system.
"""
import json
import random
import time
from locust import HttpUser, task, between, events
from .config import TEST_USER, NL_TEST_QUERIES, TEST_QUERIES


class SQLAgentUser(HttpUser):
    """
    Simulated user for load testing the SQL DB LLM Agent system.
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """
        Initialize the user session by logging in and getting a database connection.
        """
        # Login
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get available databases
            db_response = self.client.get(
                "/api/db/list",
                headers=self.headers
            )
            if db_response.status_code == 200:
                db_list = db_response.json()
                if db_list:
                    self.db_id = db_list[0]["id"]
                    
                    # Connect to database
                    self.client.post(
                        f"/api/db/connect/{self.db_id}",
                        headers=self.headers
                    )
                else:
                    self.environment.runner.quit()
        else:
            self.environment.runner.quit()
    
    @task(3)
    def execute_simple_query(self):
        """
        Execute a simple SQL query.
        """
        self.client.post(
            "/api/query/execute",
            json={
                "database_id": self.db_id,
                "sql": TEST_QUERIES["simple"]
            },
            headers=self.headers,
            name="/api/query/execute (simple)"
        )
    
    @task(2)
    def execute_medium_query(self):
        """
        Execute a medium complexity SQL query.
        """
        self.client.post(
            "/api/query/execute",
            json={
                "database_id": self.db_id,
                "sql": TEST_QUERIES["medium"]
            },
            headers=self.headers,
            name="/api/query/execute (medium)"
        )
    
    @task(1)
    def execute_complex_query(self):
        """
        Execute a complex SQL query.
        """
        self.client.post(
            "/api/query/execute",
            json={
                "database_id": self.db_id,
                "sql": TEST_QUERIES["complex"]
            },
            headers=self.headers,
            name="/api/query/execute (complex)"
        )
    
    @task(2)
    def natural_language_query(self):
        """
        Submit a natural language query.
        """
        query = random.choice(NL_TEST_QUERIES)
        response = self.client.post(
            "/api/query/natural",
            json={
                "database_id": self.db_id,
                "query": query
            },
            headers=self.headers,
            name="/api/query/natural"
        )
        
        if response.status_code == 200:
            result = response.json()
            if "query_id" in result and "generated_sql" in result:
                # Execute the generated SQL
                self.client.post(
                    "/api/query/execute",
                    json={
                        "database_id": self.db_id,
                        "query_id": result["query_id"],
                        "sql": result["generated_sql"]
                    },
                    headers=self.headers,
                    name="/api/query/execute (from NL)"
                )
    
    @task(1)
    def view_query_history(self):
        """
        View query history.
        """
        self.client.get(
            "/api/history",
            headers=self.headers,
            name="/api/history"
        )
    
    @task(1)
    def get_database_schema(self):
        """
        Get database schema.
        """
        self.client.get(
            f"/api/db/schema/{self.db_id}",
            headers=self.headers,
            name="/api/db/schema"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Set up test environment before the test starts.
    """
    print("Starting load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Clean up after the test completes.
    """
    print("Load test completed.")
    
    # Generate summary report
    from datetime import datetime
    import os
    from pathlib import Path
    from .config import RESULTS_DIR
    
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write statistics to JSON file
    stats = environment.stats.serialize_stats()
    with open(results_dir / f"load_test_stats_{timestamp}.json", "w") as f:
        json.dump(stats, f, indent=2)
    
    # Generate summary report
    total_requests = sum(stats["stats"][key]["num_requests"] for key in stats["stats"])
    total_failures = sum(stats["stats"][key]["num_failures"] for key in stats["stats"])
    avg_response_time = sum(stats["stats"][key]["avg_response_time"] * stats["stats"][key]["num_requests"] 
                           for key in stats["stats"]) / total_requests if total_requests > 0 else 0
    
    with open(results_dir / f"load_test_summary_{timestamp}.txt", "w") as f:
        f.write(f"Load Test Summary - {timestamp}\n")
        f.write(f"==================================\n\n")
        f.write(f"Total Requests: {total_requests}\n")
        f.write(f"Total Failures: {total_failures}\n")
        f.write(f"Failure Rate: {(total_failures / total_requests * 100) if total_requests > 0 else 0:.2f}%\n")
        f.write(f"Average Response Time: {avg_response_time:.2f} ms\n\n")
        
        f.write("Endpoint Statistics:\n")
        f.write("-------------------\n")
        for key in stats["stats"]:
            f.write(f"\n{key}:\n")
            f.write(f"  Requests: {stats['stats'][key]['num_requests']}\n")
            f.write(f"  Failures: {stats['stats'][key]['num_failures']}\n")
            f.write(f"  Median Response Time: {stats['stats'][key]['median_response_time']:.2f} ms\n")
            f.write(f"  90%ile Response Time: {stats['stats'][key]['response_time_percentiles']['0.9']:.2f} ms\n")
            f.write(f"  99%ile Response Time: {stats['stats'][key]['response_time_percentiles']['0.99']:.2f} ms\n")
    
    print(f"Test results saved to {results_dir}")


# If running directly, start Locust in standalone mode
if __name__ == "__main__":
    import sys
    import subprocess
    from .config import LOCUST_HOST, LOCUST_WEB_PORT, LOCUST_HEADLESS, LOAD_TEST_USERS, LOAD_TEST_DURATION, LOAD_TEST_RAMP_UP
    
    # Build command
    cmd = [
        "locust",
        "-f", __file__,
        "--host", LOCUST_HOST
    ]
    
    if LOCUST_HEADLESS:
        cmd.extend([
            "--headless",
            "-u", str(LOAD_TEST_USERS),
            "-r", str(LOAD_TEST_USERS // LOAD_TEST_RAMP_UP),
            "-t", f"{LOAD_TEST_DURATION}s"
        ])
    else:
        cmd.extend([
            "--web-port", str(LOCUST_WEB_PORT)
        ])
    
    # Run Locust
    subprocess.run(cmd)