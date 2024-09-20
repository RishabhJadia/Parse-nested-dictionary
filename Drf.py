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
