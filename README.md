# wavefront-python-sdk [![travis build status](https://travis-ci.com/wavefrontHQ/wavefront-python-sdk.svg?branch=master)](https://travis-ci.com/wavefrontHQ/wavefront-python-sdk)

This library provides support for sending metrics, histograms and opentracing spans to Wavefront via proxy or direct ingestion.

## Requirements
Python 2.7+ and Python 3.x are supported.

```
pip install wavefront_python_sdk
```

## Usage

### Send data to Wavefront via Proxy

Assume you have a running Wavefront proxy listening on at least one of metrics / direct-distribution / tracing ports and you know the proxy hostname.

#### Create a `WavefrontProxyClient`

```Python
from wavefront_python_sdk import WavefrontProxyClient

# Create Proxy Client
# host: Hostname of the Wavefront proxy, 2878 by default
# metrics_port: Metrics Port on which the Wavefront proxy is listening on
# distribution_port: Distribution Port on which the Wavefront proxy is listening on
# tracing_port: Tracing Port on which the Wavefront proxy is listening on
proxy_client = WavefrontProxyClient(proxy_host=host,
                                    metrics_port=2878,
                                    distribution_port=40000,
                                    tracing_port=30000)
```

#### Send Single Data Point

Using following functions to send one data point to Wavefront via Proxy

```python
from uuid import UUID
from wavefront_python_sdk.entities.histogram import HistogramGranularity

# 1) Send Metric to Wavefront
# Wavefront Metrics Data format:
# <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
proxy_client.send_metric(name="new york.power.usage", 
                         value=42422.0, 
                         timestamp=1533529977,
                         source="localhost", 
                         tags={"datacenter": "dc1"})

# 2) Send Direct Distribution (Histogram) to Wavefront
# Wavefront Histogram Data format:
# {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids] <histogramName> source=<source> [pointTags]
# Example: You can choose to send to atmost 3 bins - Minute/Hour/Day
# 1. Send to minute bin    =>
# "!M 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
# 2. Send to hour bin      =>
# "!H 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
# 3. Send to day bin       =>    
# "!D 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
proxy_client.send_distribution(name="request.latency", 
                               centroids=[(30, 20), (5.1, 10)],
                               histogram_granularities=
                               {HistogramGranularity.DAY,
                                HistogramGranularity.HOUR,
                                HistogramGranularity.MINUTE},
                               timestamp=1533529977,
                               source="appServer1", 
                               tags={"region": "us-west"})

# 3) Send OpenTracing Span to Wavefront
# Wavefront Tracing Span Data format:
# <tracingSpanName> source=<source> [pointTags] <start_millis> <duration_milliseconds>
# Example: "getAllUsers source=localhost
#           traceId=7b3bf470-9456-11e8-9eb6-529269fb1459
#           spanId=0313bafe-9457-11e8-9eb6-529269fb1459
#           parent=2f64e538-9457-11e8-9eb6-529269fb1459
#           application=Wavefront http.method=GET
#           1533529977 343500"
proxy_client.send_span(name="getAllUsers", 
                       start_millis=1533529977, 
                       duration_millis=343500,
                       source="localhost",
                       trace_id=UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                       span_id=UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                       parents=[UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
                       follows_from=None,
                       tags=[("application", "Wavefront"),
                             ("http.method", "GET")],
                       span_logs=None)
```

#### Send Batch Data

Using following functions to generate data points manally and send them in batch immediately via Wavefront Proxy Client

```python
from uuid import UUID
from wavefront_python_sdk.entities.histogram import HistogramGranularity
from wavefront_python_sdk.common import metric_to_line_data
from wavefront_python_sdk.common import histogram_to_line_data
from wavefront_python_sdk.common import tracing_span_to_line_data

# Using metric_to_line_data() to generate a string data in Wavefront metric format
one_metric_data = metric_to_line_data(name="new-york.power.usage",
                                      value=42422,
                                      timestamp=1493773500,
                                      source="localhost",
                                      tags={"datacenter": "dc1"}, 
                                      default_source="defaultSource")
# result of one_metric_data will be: 
# '"new-york.power.usage" 42422.0 1493773500 source="localhost" "datacenter"="dc1"\n'
batch_metric_data = [one_metric_data, one_metric_data] # List of data
# Using send_metric_now() to send list of data in once immediately
proxy_client.send_metric_now(batch_metric_data)

one_histogram_data = histogram_to_line_data(name="request.latency",
                                            centroids=[(30.0, 20), (5.1, 10)],
                                            histogram_granularities=
                                            {HistogramGranularity.MINUTE,
                                             HistogramGranularity.HOUR,
                                             HistogramGranularity.DAY},
                                            timestamp=1493773500, 
                                            source="appServer1",
                                            tags={"region": "us-west"}, 
                                            default_source ="defaultSource")
# result of one_histogram_data will be:
# '!D 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n
# !H 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n
# !M 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n'
batch_histogram_data = [one_histogram_data, one_histogram_data] # List of data
# Using send_distribution_now() to send list of data in once immediately
proxy_client.send_distribution_now(batch_histogram_data)

one_tracing_span_data = tracing_span_to_line_data(
                          name="getAllUsers", 
                          start_millis=1493773500,
                          duration_millis=343500, 
                          source="localhost",
                          trace_id=UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                          span_id=UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                          parents=[UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
                          follows_from=[UUID("5f64e538-9457-11e8-"
                                             "9eb6-529269fb1459")],
                          tags=[("application", "Wavefront"), 
                                ("http.method", "GET")],
                          span_logs=None,
                          default_source="defaultSource")
# result of one_tracing_span_data will be:
# '"getAllUsers" source="localhost" traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 spanId=0313bafe-
# 9457-11e8-9eb6-529269fb1459 parent=2f64e538-9457-11e8-9eb6-529269fb1459 followsFrom=5f64e538-
# 9457-11e8-9eb6-529269fb1459 "application"="Wavefront" "http.method"="GET" 1493773500 343500\n'
batch_span_data = [one_tracing_span_data, one_tracing_span_data] # List of data
# Using send_span_now() to send list of data in once immediately
proxy_client.send_span_now(batch_span_data)

```

#### Get failure count and close connection

```python
# If there are any failures observed while sending metrics/histograms/tracing-spans above, 
# you can get the total failure count using the below API
total_failures = proxy_client.get_failure_count();
  
# close existing connections of the client
proxy_client.close();
```



### Send data to Wavefront via Direct Ingestion

Assume you have a running Wavefront cluster and you know the server URL (example - https://mydomain.wavefront.com) and the API token.

#### Create a `WavefrontDirectClient`

```python
from wavefront_python_sdk import WavefrontDirectClient

# Create Direct Client
# server: Server address, Example: https://mydomain.wavefront.com
# token: Token with Direct Data Ingestion permission granted
# max_queue_size: Max Queue Size, size of internal data buffer for each data type. 50000 by default
# batch_size: Batch Size, amount of data sent by one API call, 10000 by default
# flush_interval_seconds: Buffer flushing interval time, 5 seconds by default
direct_client = WavefrontDirectClient(server="http://localhost:8080",
                                    token="!23",
                                    max_queue_size=50000,
                                    batch_size=10000,
                                    flush_interval_seconds=5)
```

#### Send Single Data Point

Using following functions to send one data point to Wavefront via Direct Ingestion

```python
# 1) Send Metric to Wavefront
# Wavefront Metrics Data format:
# <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
direct_client.send_metric(name="new york.power.usage", 
                         value=42422.0, 
                         timestamp=1533529977,
                         source="localhost", 
                         tags={"datacenter": "dc1"})

# 2) Send Direct Distribution (Histogram) to Wavefront
# Wavefront Histogram Data format:
# {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids] <histogramName> source=<source> [pointTags]
# Example: You can choose to send to atmost 3 bins - Minute/Hour/Day
# 1. Send to minute bin    =>
# "!M 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
# 2. Send to hour bin      =>
# "!H 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
# 3. Send to day bin       =>    
# "!D 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
direct_client.send_distribution(name="request.latency", 
                               centroids=[(30, 20), (5.1, 10)],
                               histogram_granularities=
                               {HistogramGranularity.DAY,
                                HistogramGranularity.HOUR,
                                HistogramGranularity.MINUTE},
                               timestamp=1533529977,
                               source="appServer1", 
                               tags={"region": "us-west"})

# 3) Send OpenTracing Span to Wavefront
# Wavefront Tracing Span Data format:
# <tracingSpanName> source=<source> [pointTags] <start_millis> <duration_milliseconds>
# Example: "getAllUsers source=localhost
#           traceId=7b3bf470-9456-11e8-9eb6-529269fb1459
#           spanId=0313bafe-9457-11e8-9eb6-529269fb1459
#           parent=2f64e538-9457-11e8-9eb6-529269fb1459
#           application=Wavefront http.method=GET
#           1533529977 343500"
direct_client.send_span(name="getAllUsers", 
                       start_millis=1533529977, 
                       duration_millis=343500,
                       source="localhost",
                       trace_id=UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                       span_id=UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                       parents=[UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
                       follows_from=None,
                       tags=[("application", "Wavefront"),
                             ("http.method", "GET")],
                       span_logs=None)
```

#### Send Batch Data

Using following functions to generate data points manally and send them in batch immediately via Wavefront Direct Client

```python
from uuid import UUID
from wavefront_python_sdk.entities.histogram import HistogramGranularity
from wavefront_python_sdk.common import metric_to_line_data
from wavefront_python_sdk.common import histogram_to_line_data
from wavefront_python_sdk.common import tracing_span_to_line_data

# Using metric_to_line_data() to generate a string data in Wavefront metric format
one_metric_data = metric_to_line_data(name="new-york.power.usage",
                                      value=42422,
                                      timestamp=1493773500,
                                      source="localhost",
                                      tags={"datacenter": "dc1"}, 
                                      default_source="defaultSource")
# result of one_metric_data will be: 
# '"new-york.power.usage" 42422.0 1493773500 source="localhost" "datacenter"="dc1"\n'
batch_metric_data = [one_metric_data, one_metric_data] # List of data
# Using send_metric_now() to send list of data in once immediately
direct_client.send_metric_now(batch_metric_data)

one_histogram_data = histogram_to_line_data(name="request.latency",
                                            centroids=[(30.0, 20), (5.1, 10)],
                                            histogram_granularities=
                                            {HistogramGranularity.MINUTE,
                                             HistogramGranularity.HOUR,
                                             HistogramGranularity.DAY},
                                            timestamp=1493773500, 
                                            source="appServer1",
                                            tags={"region": "us-west"}, 
                                            default_source ="defaultSource")
# result of one_histogram_data will be:
# '!D 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n
# !H 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n
# !M 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n'
batch_histogram_data = [one_histogram_data, one_histogram_data] # List of data
# Using send_distribution_now() to send list of data in once immediately
direct_client.send_distribution_now(batch_histogram_data)

one_tracing_span_data = tracing_span_to_line_data(
                          name="getAllUsers", 
                          start_millis=1493773500,
                          duration_millis=343500, 
                          source="localhost",
                          trace_id=UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                          span_id=UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                          parents=[UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
                          follows_from=[UUID("5f64e538-9457-11e8-"
                                             "9eb6-529269fb1459")],
                          tags=[("application", "Wavefront"), 
                                ("http.method", "GET")],
                          span_logs=None,
                          default_source="defaultSource")
# result of one_tracing_span_data will be:
# '"getAllUsers" source="localhost" traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 spanId=0313bafe-
# 9457-11e8-9eb6-529269fb1459 parent=2f64e538-9457-11e8-9eb6-529269fb1459 followsFrom=5f64e538-
# 9457-11e8-9eb6-529269fb1459 "application"="Wavefront" "http.method"="GET" 1493773500 343500\n'
batch_span_data = [one_tracing_span_data, one_tracing_span_data] # List of data
# Using send_span_now() to send list of data in once immediately
direct_client.send_span_now(batch_span_data)

```

#### Get failure count and manually flush buffer

```python
# If there are any failures observed while sending metrics/histograms/tracing-spans above, 
# you can get the total failure count using the below API
total_failures = direct_client.get_failure_count();

# If you want to mannally flush current buffers and send all data inside them
# Flush before you close the direct client
direct_client.flush_now()
```
