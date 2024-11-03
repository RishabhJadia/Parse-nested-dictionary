#models
from django.db import models

class Host(models.Model):
    name = models.CharField(max_length=255)

class Instance(models.Model):
    name = models.CharField(max_length=255)
    env = models.CharField(max_length=50)
    host = models.ForeignKey(Host, related_name='instances', on_delete=models.CASCADE)
    version = models.CharField(max_length=50)
    region = models.CharField(max_length=50)

#serializer.py
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Instance

class InstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instance
        fields = '__all__'  # Default to all fields

    def __init__(self, *args, **kwargs):
        # Capture 'fields' from kwargs
        fields = kwargs.pop('fields', None)
        super(InstanceSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields.split(','))  # Split fields by comma
            existing = set(self.fields.keys())  # Get model fields
            invalid_fields = allowed - existing  # Find invalid fields

            # If there are invalid fields, raise a ValidationError
            if invalid_fields:
                raise ValidationError(f"Invalid fields requested: {', '.join(invalid_fields)}")

            # Remove fields not in the allowed set
            for field_name in existing - allowed:
                self.fields.pop(field_name)

#views.py
from rest_framework import generics
from rest_framework.response import Response
from .models import Instance
from .serializers import InstanceSerializer

# View to get all instances
class InstanceListAPIView(generics.ListAPIView):
    queryset = Instance.objects.all()

    def get(self, request, *args, **kwargs):
        # Get optional 'fields' query parameter
        fields = request.query_params.get('fields', None)
        instances = self.get_queryset()
        # Pass the fields to the serializer
        serializer = InstanceSerializer(instances, many=True, fields=fields)
        return Response(serializer.data)

# View to get details of a specific instance by ID
class InstanceDetailAPIView(generics.RetrieveAPIView):
    queryset = Instance.objects.all()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        # Get optional 'fields' query parameter
        fields = request.query_params.get('fields', None)
        # Pass the fields to the serializer
        serializer = InstanceSerializer(instance, fields=fields)
        return Response(serializer.data)

# View to get all instances filtered by environment
class InstanceByEnvAPIView(generics.ListAPIView):
    serializer_class = InstanceSerializer

    def get_queryset(self):
        env = self.kwargs['env']  # Get the environment from the URL
        return Instance.objects.filter(env=env)

    def get(self, request, *args, **kwargs):
        # Get optional 'fields' query parameter
        fields = request.query_params.get('fields', None)
        instances = self.get_queryset()
        # Pass the fields to the serializer
        serializer = InstanceSerializer(instances, many=True, fields=fields)
        return Response(serializer.data)
#urls.py
from django.urls import path
from .views import InstanceListAPIView, InstanceDetailAPIView, InstanceByEnvAPIView

urlpatterns = [
    path('instances/', InstanceListAPIView.as_view(), name='instance-list'),  # Get all instances
    path('instances/<int:pk>/', InstanceDetailAPIView.as_view(), name='instance-detail'),  # Get instance by ID
    path('instances/env/<str:env>/', InstanceByEnvAPIView.as_view(), name='instance-by-env'),  # Get instances by environment
]
---------------------------------------------------------------------------------------------
from django.db.models import Prefetch, Q
from rest_framework import generics
from .models import Machine, Host
from .serializers import MachineSerializer

class MachineListView(generics.ListAPIView):
    serializer_class = MachineSerializer

    def get_queryset(self):
        # Retrieve query parameters for filtering
        host_filter_criteria = {
            'status': self.request.query_params.get('host_status'),
            'environment': self.request.query_params.get('host_environment'),
            'country': self.request.query_params.get('host_country'),
            'datacenter': self.request.query_params.get('host_datacenter'),
            'hosts': self.request.query_params.get('hosts')  # New parameter for hosts
        }

        # Build a Q filter for the Host model
        host_filter = Q()
        for field, value in host_filter_criteria.items():
            if value:
                if field == 'hosts':
                    # Handle case where hosts is null or contains comma-separated values
                    if value == 'null':
                        host_filter &= Q(**{f"{field}__isnull": True})
                    else:
                        # Split comma-separated values into a list and create Q objects
                        host_names = [name.strip() for name in value.split(',')]
                        host_filter &= Q(name__in=host_names)
                elif value == 'null':
                    host_filter &= Q(**{f"{field}__isnull": True})
                else:
                    host_filter &= Q(**{field: value})

        # Base queryset for Machine
        if host_filter_criteria['hosts'] == 'null':
            # Filter machines with no hosts
            queryset = Machine.objects.filter(hosts__isnull=True)
        else:
            # Prefetch related hosts and apply filters if hosts should not be empty
            queryset = Machine.objects.prefetch_related(
                Prefetch(
                    'hosts',
                    queryset=Host.objects.filter(host_filter).only('name', 'datacenter')
                )
            ).filter(hosts__in=Host.objects.filter(host_filter)).distinct()

        return queryset

    def get_serializer_context(self):
        # Pass the filter values to the serializer context
        context = super().get_serializer_context()
        context.update({
            'host_status': self.request.query_params.get('host_status'),
            'host_environment': self.request.query_params.get('host_environment'),
            'host_country': self.request.query_params.get('host_country'),
            'host_datacenter': self.request.query_params.get('host_datacenter'),
            'hosts': self.request.query_params.get('hosts'),  # New context for hosts
        })
        return context
---------------------------------------------------------------
from django.db.models import Prefetch, Q
from rest_framework import generics
from .models import Job, Machine, Host

class JobListView(generics.ListAPIView):
    serializer_class = JobSerializer

    def get_queryset(self):
        # Retrieve query parameters for filtering
        machine_null = self.request.query_params.get('machines')
        
        # Define host attribute filters
        host_filter_criteria = {
            'status': self.request.query_params.get('host_status'),
            'environment': self.request.query_params.get('host_environment'),
            'country': self.request.query_params.get('host_country'),
            'datacenter': self.request.query_params.get('host_datacenter')
        }

        # Build a Q filter for the Host model
        host_filter = Q()
        for field, value in host_filter_criteria.items():
            if value:
                if value == 'null':
                    host_filter &= Q(**{f"{field}__isnull": True})
                else:
                    host_filter &= Q(**{field: value})

        # Create a machine filter for machines with specific hosts
        machine_filter = Q()
        if machine_null == 'null':
            # If machines=null in query param, filter for jobs with no machines
            machine_filter &= Q(machines__isnull=True)
        else:
            # Prefetch machines with only hosts that match the host filter criteria
            filtered_machines = Machine.objects.prefetch_related(
                Prefetch(
                    'hosts',
                    queryset=Host.objects.filter(host_filter),
                    to_attr='prefetched_hosts'
                )
            ).filter(hosts__in=Host.objects.filter(host_filter))  # Filter machines based on host criteria
            
            # Apply machine filter for jobs with relevant machines
            machine_filter &= Q(machines__in=filtered_machines)

        # Get jobs matching the machine filter or without machines if specified
        queryset = Job.objects.filter(machine_filter).distinct().prefetch_related(
            Prefetch('machines', queryset=filtered_machines if machine_null != 'null' else Machine.objects.none())
        )

        return queryset

    def get_serializer_context(self):
        # Pass the filter values to the serializer context
        context = super().get_serializer_context()
        context.update({
            'host_status': self.request.query_params.get('host_status'),
            'host_environment': self.request.query_params.get('host_environment'),
            'host_country': self.request.query_params.get('host_country'),
            'host_datacenter': self.request.query_params.get('host_datacenter'),
        })
        return context
---------------------------------------
from django.db.models import Prefetch, Q
from rest_framework import generics
from .models import Job, Machine, Host, Instance

class JobListView(generics.ListAPIView):
    serializer_class = JobSerializer

    def get_queryset(self):
        # Retrieve query parameters for filtering Job, Instance, and Machine attributes
        machine_null = self.request.query_params.get('machines')
        
        # Job attribute filters
        job_filters = {
            'name': self.request.query_params.get('job_name'),
            'job_type': self.request.query_params.get('job_type'),
        }
        
        # Instance attribute filters
        instance_filters = {
            'name': self.request.query_params.get('instance_name'),
            'env': self.request.query_params.get('instance_env'),
        }

        # Build Job filters
        job_filter = Q()
        for field, value in job_filters.items():
            if value:
                job_filter &= Q(**{f"{field}": value})

        # Build Instance filters
        instance_filter = Q()
        for field, value in instance_filters.items():
            if value:
                instance_filter &= Q(**{f"instance__{field}": value})
        
        # Host attribute filters
        host_filter_criteria = {
            'status': self.request.query_params.get('host_status'),
            'environment': self.request.query_params.get('host_environment'),
            'country': self.request.query_params.get('host_country'),
            'datacenter': self.request.query_params.get('host_datacenter'),
        }

        # Build a Q filter for the Host model
        host_filter = Q()
        for field, value in host_filter_criteria.items():
            if value:
                if value == 'null':
                    host_filter &= Q(**{f"{field}__isnull": True})
                else:
                    host_filter &= Q(**{field: value})

        # Initialize an empty queryset for filtered_machines
        filtered_machines = Machine.objects.none()

        if machine_null != 'null':
            # Prefetch machines with only hosts that match the host filter criteria
            filtered_machines = Machine.objects.prefetch_related(
                Prefetch(
                    'hosts',
                    queryset=Host.objects.filter(host_filter),
                    to_attr='prefetched_hosts'
                )
            ).filter(hosts__in=Host.objects.filter(host_filter))  # Filter machines based on host criteria

        # Combine job, instance, and machine filters
        queryset = Job.objects.filter(
            job_filter & instance_filter
        ).filter(
            Q(machines__isnull=True) if machine_null == 'null' else Q(machines__in=filtered_machines)
        ).distinct().prefetch_related(
            Prefetch('machines', queryset=filtered_machines)
        )

        return queryset

    def get_serializer_context(self):
        # Pass the filter values to the serializer context
        context = super().get_serializer_context()
        context.update({
            'host_status': self.request.query_params.get('host_status'),
            'host_environment': self.request.query_params.get('host_environment'),
            'host_country': self.request.query_params.get('host_country'),
            'host_datacenter': self.request.query_params.get('host_datacenter'),
        })
        return context
---------------------------------------------------------------------------
from django.db.models import Count
from django.utils import timezone
from .models import Job, JobMetrics

def update_job_metrics():
    # Aggregate job count by host country
    country_counts = Job.objects.values('machine__hosts__country').annotate(
        job_country_count=Count('machine__hosts__country')
    ).values('machine__hosts__country', 'job_country_count')

    # Aggregate job count by host datacenter
    datacenter_counts = Job.objects.values('machine__hosts__datacenter').annotate(
        job_datacenter_count=Count('machine__hosts__datacenter')
    ).values('machine__hosts__datacenter', 'job_datacenter_count')

    # Fetch existing metrics into memory
    existing_metrics = JobMetrics.objects.all()
    existing_metrics_dict = { (m.country, m.datacenter): m for m in existing_metrics }

    # List for bulk create/update
    bulk_create_entries = []
    bulk_update_entries = []

    # Update or create the JobMetrics table with country counts
    for country_data in country_counts:
        country = country_data['machine__hosts__country']
        job_country_count = country_data['job_country_count']
        key = (country, None)  # Tuple key for country-only metrics
        
        if key in existing_metrics_dict:
            metrics = existing_metrics_dict[key]
            metrics.job_country_count = job_country_count
            metrics.last_updated = timezone.now()
            bulk_update_entries.append(metrics)
        else:
            bulk_create_entries.append(JobMetrics(
                country=country,
                job_country_count=job_country_count,
                last_updated=timezone.now()
            ))

    # Update or create the JobMetrics table with datacenter counts
    for datacenter_data in datacenter_counts:
        datacenter = datacenter_data['machine__hosts__datacenter']
        job_datacenter_count = datacenter_data['job_datacenter_count']
        key = (None, datacenter)  # Tuple key for datacenter-only metrics
        
        if key in existing_metrics_dict:
            metrics = existing_metrics_dict[key]
            metrics.job_datacenter_count = job_datacenter_count
            metrics.last_updated = timezone.now()
            bulk_update_entries.append(metrics)
        else:
            bulk_create_entries.append(JobMetrics(
                datacenter=datacenter,
                job_datacenter_count=job_datacenter_count,
                last_updated=timezone.now()
            ))

    # Perform bulk create and update
    JobMetrics.objects.bulk_create(bulk_create_entries)
    JobMetrics.objects.bulk_update(bulk_update_entries, ['job_country_count', 'job_datacenter_count', 'last_updated'])

