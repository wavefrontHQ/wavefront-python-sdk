from __future__ import absolute_import, division, print_function

import re
import io
from gzip import GzipFile
import threading


class AtomicCounter(object):
    """
    An atomic, thread-safe incrementing counter.
    """

    def __init__(self, initial=0):
        self.value = initial
        self._lock = threading.Lock()

    def increment(self, num=1):
        """
        Increment atomic counter value
        @param num: Num to be increased, 1 by default
        @return: Current value after increment
        """
        with self._lock:
            self.value += num
            return self.value


def chunks(data_list, batch_size):
    """
    Split list of data into chunks with fixed batch size
    @param data_list: List of data
    @param batch_size: Batch size of each chunk
    @return: Return a lazy generator object for iteration
    """
    for i in range(0, len(data_list), batch_size):
        yield data_list[i:i + batch_size]


def gzip_compress(data, compresslevel=9):
    """
    Compress data using GZIP
    @param data: Data to compress
    @param compresslevel: Compress Level
    @return: Compressed data
    """
    buf = io.BytesIO()
    with GzipFile(fileobj=buf, mode='wb', compresslevel=compresslevel) as f:
        f.write(data)
    return buf.getvalue()


def sanitize(s):
    """
    Sanitize a string, replace whitespace with "-"
    @param s: Input string
    @return: Sanitized string
    """
    whitespace_sanitized = re.sub(r"[\s]+", "-", s)
    if "\"" in whitespace_sanitized:
        return "\"" + re.sub(r"[\"]+", '\\\\\"', whitespace_sanitized) + "\""
    else:
        return "\"" + whitespace_sanitized + "\""


def is_blank(s):
    """
    Check is a string is black or not, either none or only contains whitespace
    @param s: String to be checked
    @return: Is blank or not
    """
    return s is None or len(s) == 0 or s.isspace()
    # return len(re.sub(r"[\s]+", "", s)) == 0


def metric_to_line_data(name, value, timestamp, source, tags, default_source):
    """
    Metric Data to String
    Wavefront Metrics Data format
    <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
    Example: "new-york.power.usage 42422 1533531013 source=localhost
              datacenter=dc1"
    @param name: Metric Name
    @type name: str
    @param value: Metric Value
    @type value: float
    @param timestamp: Timestamp
    @type timestamp: long
    @param source: Source
    @type source: str
    @param tags: Tags
    @type tags: dict
    @param default_source:
    @type default_source: str
    @return: String
    """
    if is_blank(name):
        raise ValueError("Metrics name cannot be blank")

    if is_blank(source):
        source = default_source

    str_builder = [sanitize(name), float(value)]
    if timestamp is not None:
        str_builder.append(int(timestamp))
    str_builder.append("source=" + sanitize(source))
    if tags is not None:
        for key in tags:
            if is_blank(key):
                raise ValueError("Metric point tag key cannot be blank")
            if is_blank(tags[key]):
                raise ValueError("Metric point tag value cannot be blank")
            str_builder.append(sanitize(key) + '=' + sanitize(tags[key]))
    return ' '.join('{0}'.format(s) for s in str_builder) + "\n"


def histogram_to_line_data(name, centroids, histogram_granularities, timestamp,
                           source, tags, default_source):
    """
    Wavefront Histogram Data format
    {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids] <histogramName>
    source=<source> [pointTags]
    Example: "!M 1533531013 #20 30.0 #10 5.1 request.latency source=appServer1
              region=us-west"
    @param name: Histogram Name
    @type name: str
    @param centroids: List of centroids(pairs)
    @type centroids: list
    @param histogram_granularities: Histogram Granularities
    @type histogram_granularities: set
    @param timestamp: Timestamp
    @type timestamp: long
    @param source: Source
    @type source: str
    @param tags: Tags
    @type tags: dict
    @param default_source: Default Source
    @type default_source: str
    @return: String data of Histogram
    """
    if is_blank(name):
        raise ValueError("Histogram name cannot be blank")

    if not histogram_granularities:
        raise ValueError("Histogram granularities cannot be null or empty")

    if not centroids:
        raise ValueError("A distribution should have at least one centroid")

    if is_blank(source):
        source = default_source

    line_builder = []
    for histogram_granularity in histogram_granularities:
        str_builder = [histogram_granularity]
        if timestamp is not None:
            str_builder.append(int(timestamp))
        for centroid_1, centroid_2 in centroids:
            str_builder.append("#" + repr(centroid_2))
            str_builder.append(centroid_1)
        str_builder.append(sanitize(name))
        str_builder.append("source=" + sanitize(source))
        if tags is not None:
            for key in tags:
                if is_blank(key):
                    raise ValueError("Histogram tag key cannot be blank")
                if is_blank(tags[key]):
                    raise ValueError("Histogram tag value cannot be blank")
                str_builder.append(sanitize(key) + '=' + sanitize(tags[key]))
        line_builder.append(' '.join('{0}'.format(s) for s in str_builder))
    return '\n'.join('{0}'.format(line) for line in line_builder) + "\n"


def tracing_span_to_line_data(name, start_millis, duration_millis, source,
                              trace_id, span_id, parents, follows_from, tags,
                              span_logs, default_source):
    """
    Wavefront Tracing Span Data format
    <tracingSpanName> source=<source> [pointTags] <start_millis>
    <duration_milli_seconds>
    Example: "getAllUsers source=localhost
              traceId=7b3bf470-9456-11e8-9eb6-529269fb1459
              spanId=0313bafe-9457-11e8-9eb6-529269fb1459
              parent=2f64e538-9457-11e8-9eb6-529269fb1459
              application=Wavefront http.method=GET
              1533531013 343500"
    @param name: Span Name
    @type name: str
    @param start_millis: Start time
    @type start_millis: long
    @param duration_millis: Duration time
    @type duration_millis: long
    @param source: Source
    @type source: str
    @param trace_id: Trace ID
    @type trace_id: UUID
    @param span_id: Span ID
    @type span_id: UUID
    @param parents: Parents Span ID
    @type parents: List of UUID
    @param follows_from: Follows Span ID
    @type follows_from: List of UUID
    @param tags: Tags
    @type tags: list
    @param span_logs: Span Log
    @param default_source: Default Source
    @type default_source: str
    @return: String data of tracing span
    """
    if is_blank(name):
        raise ValueError("Span name cannot be blank")

    if is_blank(source):
        source = default_source

    str_builder = [sanitize(name),
                   "source=" + sanitize(source),
                   "traceId=" + str(trace_id),
                   "spanId=" + str(span_id)]
    if parents is not None:
        for uuid in parents:
            str_builder.append("parent=" + str(uuid))
    if follows_from is not None:
        for uuid in follows_from:
            str_builder.append("followsFrom=" + str(uuid))
    if tags is not None:
        for key, val in tags:
            if is_blank(key):
                raise ValueError("Span tag key cannot be blank")
            if is_blank(val):
                raise ValueError("Span tag val cannot be blank")
            str_builder.append(sanitize(key) + "=" + sanitize(val))
    str_builder.append(start_millis)
    str_builder.append(duration_millis)
    return ' '.join('{0}'.format(s) for s in str_builder) + "\n"
