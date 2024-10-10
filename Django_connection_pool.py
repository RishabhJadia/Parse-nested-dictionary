views. py
from django.http import JsonResponse
from django.db import connection
import time

def test_database_queries(request):
    start_time = time.time()
    queries_count = 100  # Simulate 100 database queries

    with connection.cursor() as cursor:
        for _ in range(queries_count):
            cursor.execute("SELECT COUNT(*) FROM your_table_name")  # Replace with your table
            row_count = cursor.fetchone()

    end_time = time.time()
    total_time = end_time - start_time

    return JsonResponse({
        'queries_executed': queries_count,
        'total_time_seconds': total_time,
 

urls.py
from django.urls import path
from .views import test_database_queries

urlpatterns = [
    path('test-db/', test_database_queries),
]'row_count': row_count[0],
    })

pip install django-db-geventpool psycopg2
settings.py

# settings.py (Without connection pooling)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'your_cockroachdb_host',
        'PORT': '26257',
    }
}
# settings.py (With connection pooling)
DATABASES = {
    'default': {
        'ENGINE': 'django_db_geventpool.backends.postgresql_psycopg2',
        'NAME': 'your_db_name',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'your_cockroachdb_host',
        'PORT': '26257',
        'OPTIONS': {
            'MAX_CONNS': 20,  # Max open connections in the pool
            'REUSE_CONNS': 10,  # Max number of times to reuse a connection
        },
    }
}
