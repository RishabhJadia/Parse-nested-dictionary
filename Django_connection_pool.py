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
--------------------------------------------------------------------------------------------------
from django.db import transaction
from time import sleep
from random import uniform
from cockroachdb.errors import TransactionRetryWithProtoRefreshError

MAX_RETRIES = 5  # Maximum number of retries for a transaction
RETRY_DELAY_MIN = 0.1  # Minimum delay between retries in seconds
RETRY_DELAY_MAX = 1.0  # Maximum delay between retries in seconds

def bulk_insert_with_retry(record_df):
    to_create = []
    for _, row in record_df.iterrows():  # Assuming record_df is a DataFrame
        to_create.append(MyModel(**row.to_dict()))

    retries = 0

    while retries < MAX_RETRIES:
        try:
            with transaction.atomic():
                MyModel.objects.bulk_create(to_create, batch_size=15000)
            # Break out of the loop if the transaction is successful
            break
        except TransactionRetryWithProtoRefreshError:
            retries += 1
            # Backoff and retry
            if retries < MAX_RETRIES:
                delay = uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
                print(f"Transaction retry {retries}/{MAX_RETRIES}. Retrying in {delay:.2f} seconds...")
                sleep(delay)
            else:
                print("Max retries reached. Failing.")
                raise  # Reraise the exception if max retries exceeded
