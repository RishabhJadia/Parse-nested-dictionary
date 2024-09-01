from django.db import transaction
from your_app.models import Host, Seal, Instance
import pandas as pd

# Example list of dictionaries
host_data = [
    {'host': 'host1', 'environment': 'prod', 'seal': 'seal1'},
    {'host': 'host1', 'environment': 'prod', 'seal': 'seal2'},
    {'host': 'host1', 'environment': 'test', 'seal': 'seal1'},
    # Add more dictionaries as needed
]

# Start a transaction to ensure atomicity
with transaction.atomic():
    for entry in host_data:
        host_name = entry['host']
        environment = entry['environment']
        seal_name = entry['seal']
        
        # Fetch or create Seal
        seal, _ = Seal.objects.get_or_create(name=seal_name)
        
        # Check if host exists with null seal and environment
        host = Host.objects.filter(name=host_name, seal__isnull=True, environment__isnull=True).first()
        
        if host:
            # Update the existing host with the new seal and environment
            host.seal = seal
            host.environment = environment
            host.save()
            print(f"Updated existing host {host_name} with environment {environment} and seal {seal_name}.")
        
        else:
            # Check if host exists with non-null seal and environment
            existing_host = Host.objects.filter(name=host_name, seal__isnull=False, environment__isnull=False).first()
            
            if existing_host:
                # Create a new host as a copy of the existing one, but with the new seal and environment
                new_host = Host.objects.create(
                    name=existing_host.name,
                    seal=seal,
                    environment=environment,
                )
                # Copy the Many-to-Many relationships for instances from the existing host
                new_host.instance.set(existing_host.instance.all())
                print(f"Created new host {host_name} with environment {environment} and seal {seal_name}.")
            else:
                print(f"No matching host found for {host_name}.")
