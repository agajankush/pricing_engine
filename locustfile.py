from locust import HttpUser, task, between
import random

class PricingEngineUser(HttpUser):
    # Simulate a pause between requests
    wait_time = between(0.5, 2.0)
    
    @task(1) # Primary Task to test
    def get_dynamic_price(self):
        request_data = {
            "product_id": f"P-{random.randint(100, 999)}",
            "user_location": random.choice(["NY", "LA", "MIA"]),
            "is_prime_member": random.choice([True, False])
        }
        
        # Test the core concurrent endpoint
        response = self.client.post(
            "/api/v1/price",
            json=request_data,
            name="/api/v1/price" # Groups all the results under one metric
        )
        
        # Validation checks
        if response.status_code != 200:
            response.failure(f"API Failed with STatus Code {response.status_code}")